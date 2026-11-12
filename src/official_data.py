import csv
import calendar
from datetime import date
from pathlib import Path

from src.compensation import load_grade_bands
from src.models import Employee, Goal, Rating


INVALID_STATUSES = {"INVALID_WEIGHTS", "INVALID_RATING"}


def _read_rows(path, required_columns):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not set(required_columns).issubset(
            reader.fieldnames
        ):
            raise ValueError(
                f"{Path(path).name} must contain columns: "
                f"{', '.join(required_columns)}"
            )
        return list(reader)


def _integer(value, field_name, minimum=None, maximum=None):
    try:
        parsed = int(value.strip())
    except (AttributeError, TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer")
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    if maximum is not None and parsed > maximum:
        raise ValueError(f"{field_name} must be at most {maximum}")
    return parsed


def _subtract_months(end_date, months):
    month_index = end_date.year * 12 + end_date.month - 1 - months
    year, month_index = divmod(month_index, 12)
    month = month_index + 1
    day = min(end_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def load_official_data(
    employees_path,
    goals_path,
    ratings_path,
    grade_bands_path,
    units_path,
    appraisal_cutoff_date,
):
    """Load the official PS-057 CSV schemas and retain per-employee errors."""
    employee_rows = _read_rows(
        employees_path,
        (
            "emp_id", "name", "unit", "grade", "basic_salary",
            "date_of_joining", "manager_id", "months_in_grade",
            "previous_year_rating", "role_band",
        ),
    )
    employees = {}
    statuses = {}

    for row in employee_rows:
        employee_id = row["emp_id"].strip()
        if not employee_id or employee_id in employees:
            raise ValueError(f"Invalid or duplicate employee ID: {employee_id!r}")
        grade = row["grade"].strip().upper()
        try:
            basic_salary = float(row["basic_salary"])
        except (TypeError, ValueError):
            raise ValueError(f"{employee_id}: basic_salary must be numeric")
        if basic_salary <= 0:
            raise ValueError(f"{employee_id}: basic_salary must be positive")

        try:
            joining_date = date.fromisoformat(row["date_of_joining"].strip())
        except (AttributeError, TypeError, ValueError):
            raise ValueError(f"{employee_id}: invalid date_of_joining")

        months_in_grade = _integer(
            row["months_in_grade"], f"{employee_id}.months_in_grade", 0
        )
        previous_rating = _integer(
            row["previous_year_rating"],
            f"{employee_id}.previous_year_rating",
            1,
            5,
        )
        if grade not in {f"G{number}" for number in range(1, 8)}:
            raise ValueError(f"{employee_id}: invalid grade {grade!r}")

        employees[employee_id] = Employee(
            employee_id=employee_id,
            business_unit=row["unit"].strip(),
            grade=grade,
            basic_salary=basic_salary,
            joining_date=joining_date,
            manager_id=row["manager_id"].strip(),
            current_role_band=row["role_band"].strip(),
            grade_start_date=_subtract_months(
                appraisal_cutoff_date, months_in_grade
            ),
            previous_final_rating=previous_rating,
            months_in_grade=months_in_grade,
        )

    goals = []
    goal_keys = set()
    goal_weight_totals = {employee_id: 0 for employee_id in employees}
    for row in _read_rows(
        goals_path, ("emp_id", "goal_id", "goal_title", "weight")
    ):
        employee_id = row["emp_id"].strip()
        goal_id = row["goal_id"].strip()
        if employee_id not in employees:
            raise ValueError(f"Goal references unknown employee: {employee_id}")
        key = employee_id, goal_id
        if not goal_id or key in goal_keys:
            raise ValueError(f"Invalid or duplicate goal: {key}")
        goal_keys.add(key)
        weight = _integer(row["weight"], f"{employee_id}.{goal_id}.weight", 1, 100)
        goal_weight_totals[employee_id] += weight
        goals.append(
            Goal(employee_id, goal_id, row["goal_title"].strip(), weight)
        )

    for employee_id, total in goal_weight_totals.items():
        if total != 100:
            statuses[employee_id] = "INVALID_WEIGHTS"

    ratings = []
    seen_ratings = set()
    rated_goal_keys = set()
    competency_employees = set()
    for row_number, row in enumerate(
        _read_rows(
            ratings_path,
            ("emp_id", "item_type", "item_id", "self_rating", "manager_rating"),
        ),
        start=2,
    ):
        employee_id = row["emp_id"].strip()
        item_type = row["item_type"].strip().upper()
        item_id = row["item_id"].strip()
        if employee_id not in employees:
            raise ValueError(
                f"ratings.csv line {row_number}: unknown employee {employee_id}"
            )
        key = employee_id, item_type, item_id
        if key in seen_ratings:
            continue
        seen_ratings.add(key)

        try:
            self_rating = _integer(
                row["self_rating"], f"ratings.csv line {row_number} self_rating", 1, 5
            )
            manager_rating = _integer(
                row["manager_rating"],
                f"ratings.csv line {row_number} manager_rating",
                1,
                5,
            )
        except ValueError:
            statuses[employee_id] = "INVALID_RATING"
            continue

        if item_type not in {"GOAL", "COMPETENCY"} or not item_id:
            statuses[employee_id] = "INVALID_RATING"
            continue
        if item_type == "GOAL":
            if (employee_id, item_id) not in goal_keys:
                statuses[employee_id] = "INVALID_RATING"
                continue
            rated_goal_keys.add((employee_id, item_id))
        else:
            competency_employees.add(employee_id)

        ratings.append(
            Rating(
                employee_id,
                item_type,
                item_id,
                self_rating,
                manager_rating,
            )
        )

    for goal_key in goal_keys - rated_goal_keys:
        statuses[goal_key[0]] = "INVALID_RATING"
    for employee_id in employees.keys() - competency_employees:
        statuses[employee_id] = "INVALID_RATING"

    grade_bands = load_grade_bands(grade_bands_path)
    unit_rows = _read_rows(
        units_path, ("unit", "increment_budget_annual", "unit_head")
    )
    budgets = {}
    for row in unit_rows:
        unit = row["unit"].strip()
        if not unit or unit in budgets:
            raise ValueError(f"Invalid or duplicate unit budget: {unit!r}")
        try:
            budget = float(row["increment_budget_annual"])
        except (TypeError, ValueError):
            raise ValueError(f"{unit}: increment budget must be numeric")
        if budget < 0:
            raise ValueError(f"{unit}: increment budget cannot be negative")
        budgets[unit] = budget

    missing_units = {
        employee.business_unit for employee in employees.values()
    } - budgets.keys()
    if missing_units:
        raise ValueError(
            f"Missing unit budgets: {', '.join(sorted(missing_units))}"
        )

    return employees, goals, ratings, statuses, grade_bands, budgets
