import csv
import calendar
import json
from datetime import date
from math import isfinite
from pathlib import Path

from src.compensation import load_grade_bands
from src.models import Employee, Goal, Rating


INVALID_STATUSES = {"INVALID_WEIGHTS", "INVALID_RATING"}
VALID_UNITS = {
    "ENGINEERING",
    "FINANCE",
    "HR",
    "LEGAL",
    "OPERATIONS",
    "SALES",
}
VALID_ROLE_BANDS = {"IC", "LEAD", "MANAGER"}


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
        if any(not name for name in reader.fieldnames):
            raise ValueError(f"{Path(path).name} has a blank column name")
        if len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"{Path(path).name} has duplicate column names")
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


def _parse_competency_list(value, field_name, catalog_ids=None, allow_empty=False):
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of competency IDs")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field_name} contains an empty or invalid ID")
    competency_ids = [item.strip() for item in value]
    if len(competency_ids) != len(set(competency_ids)):
        raise ValueError(f"{field_name} contains duplicate competency IDs")
    if not allow_empty and not competency_ids:
        raise ValueError(f"{field_name} must not be empty")
    if catalog_ids is not None:
        unknown_ids = set(competency_ids) - catalog_ids
        if unknown_ids:
            raise ValueError(
                f"{field_name} contains unknown competency IDs: "
                f"{', '.join(sorted(unknown_ids))}"
            )
    return set(competency_ids)


def load_competency_catalog(path, employee_ids):
    """Load an explicit competency catalog and its employee requirements."""
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8-sig") as file:
            catalog = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{path.name} must contain valid JSON: {error.msg}"
        )

    if not isinstance(catalog, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    if catalog.get("status") not in {"PROVISIONAL", "OFFICIAL"}:
        raise ValueError(
            f"{path.name} status must be PROVISIONAL or OFFICIAL"
        )
    if not isinstance(catalog.get("provenance"), str) or not (
        catalog["provenance"].strip()
    ):
        raise ValueError(f"{path.name} must document its provenance")

    catalog_ids = _parse_competency_list(
        catalog.get("competency_ids"),
        "competency_ids",
    )
    default_required = _parse_competency_list(
        catalog.get("default_required_competencies"),
        "default_required_competencies",
        catalog_ids,
        allow_empty=True,
    )

    employee_requirements = catalog.get(
        "employee_required_competencies", {}
    )
    if not isinstance(employee_requirements, dict):
        raise ValueError(
            "employee_required_competencies must be an object"
        )
    if any(
        not isinstance(employee_id, str) or not employee_id.strip()
        for employee_id in employee_requirements
    ):
        raise ValueError(
            "employee_required_competencies contains an invalid employee ID"
        )
    unknown_employees = set(employee_requirements) - set(employee_ids)
    if unknown_employees:
        raise ValueError(
            "Competency requirements reference unknown employees: "
            f"{', '.join(sorted(unknown_employees))}"
        )

    requirements = {}
    for employee_id in employee_ids:
        field_name = f"employee_required_competencies.{employee_id}"
        employee_required = (
            _parse_competency_list(
                employee_requirements[employee_id],
                field_name,
                catalog_ids,
            )
            if employee_id in employee_requirements
            else default_required
        )
        if not employee_required:
            raise ValueError(
                f"{field_name} has no required competency IDs"
            )
        requirements[employee_id] = employee_required

    return catalog_ids, requirements


def load_official_data(
    employees_path,
    goals_path,
    ratings_path,
    grade_bands_path,
    units_path,
    appraisal_cutoff_date,
    competency_catalog_path=None,
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
        employee_id = (row.get("emp_id") or "").strip()
        if not employee_id or employee_id in employees:
            raise ValueError(f"Invalid or duplicate employee ID: {employee_id!r}")
        grade = (row.get("grade") or "").strip().upper()
        name = (row.get("name") or "").strip()
        unit = (row.get("unit") or "").strip().upper()
        manager_id = (row.get("manager_id") or "").strip()
        role_band = (row.get("role_band") or "").strip().upper()
        if not name or not unit or not manager_id or not role_band:
            raise ValueError(
                f"{employee_id}: name, unit, manager_id and role_band "
                "are required"
            )
        if unit not in VALID_UNITS:
            raise ValueError(f"{employee_id}: invalid unit {unit!r}")
        if role_band not in VALID_ROLE_BANDS:
            raise ValueError(
                f"{employee_id}: invalid role_band {role_band!r}"
            )
        try:
            basic_salary = float(row["basic_salary"])
        except (TypeError, ValueError):
            raise ValueError(f"{employee_id}: basic_salary must be numeric")
        if not isfinite(basic_salary) or basic_salary <= 0:
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
            business_unit=unit,
            grade=grade,
            basic_salary=basic_salary,
            joining_date=joining_date,
            manager_id=manager_id,
            current_role_band=role_band,
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
        employee_id = (row.get("emp_id") or "").strip()
        goal_id = (row.get("goal_id") or "").strip()
        goal_title = (row.get("goal_title") or "").strip()
        if employee_id not in employees:
            raise ValueError(f"Goal references unknown employee: {employee_id}")
        key = employee_id, goal_id
        if not goal_id or not goal_title or key in goal_keys:
            raise ValueError(f"Invalid or duplicate goal: {key}")
        goal_keys.add(key)
        weight = _integer(row["weight"], f"{employee_id}.{goal_id}.weight", 1, 100)
        goal_weight_totals[employee_id] += weight
        goals.append(
            Goal(employee_id, goal_id, goal_title, weight)
        )

    for employee_id, total in goal_weight_totals.items():
        if total != 100:
            statuses[employee_id] = "INVALID_WEIGHTS"

    catalog_path = competency_catalog_path or Path(
        ratings_path
    ).with_name("competency_catalog.json")
    competency_ids, required_competencies = load_competency_catalog(
        catalog_path, employees
    )
    ratings = []
    seen_ratings = set()
    rated_goal_keys = set()
    rated_competencies = {employee_id: set() for employee_id in employees}
    for row_number, row in enumerate(
        _read_rows(
            ratings_path,
            ("emp_id", "item_type", "item_id", "self_rating", "manager_rating"),
        ),
        start=2,
    ):
        employee_id = (row.get("emp_id") or "").strip()
        item_type = (row.get("item_type") or "").strip().upper()
        item_id = (row.get("item_id") or "").strip()
        if employee_id not in employees:
            raise ValueError(
                f"ratings.csv line {row_number}: unknown employee {employee_id}"
            )
        key = employee_id, item_type, item_id
        if key in seen_ratings:
            if item_type == "COMPETENCY":
                statuses[employee_id] = "INVALID_RATING"
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
            if item_id not in competency_ids:
                statuses[employee_id] = "INVALID_RATING"
                continue
            rated_competencies[employee_id].add(item_id)

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
    for employee_id, required_ids in required_competencies.items():
        if required_ids - rated_competencies[employee_id]:
            statuses[employee_id] = "INVALID_RATING"

    grade_bands = load_grade_bands(grade_bands_path)
    unit_rows = _read_rows(
        units_path, ("unit", "increment_budget_annual", "unit_head")
    )
    budgets = {}
    for row in unit_rows:
        unit = (row.get("unit") or "").strip()
        if not unit or unit in budgets:
            raise ValueError(f"Invalid or duplicate unit budget: {unit!r}")
        try:
            budget = float(row["increment_budget_annual"])
        except (TypeError, ValueError):
            raise ValueError(f"{unit}: increment budget must be numeric")
        if not isfinite(budget) or budget < 0:
            raise ValueError(
                f"{unit}: increment budget must be finite and non-negative"
            )
        budgets[unit] = budget

    missing_units = {
        employee.business_unit for employee in employees.values()
    } - budgets.keys()
    if missing_units:
        raise ValueError(
            f"Missing unit budgets: {', '.join(sorted(missing_units))}"
        )

    return employees, goals, ratings, statuses, grade_bands, budgets
