import csv
from datetime import date
from pathlib import Path

from src.models import Employee, Goal, Rating


VALID_GRADES = {f"G{i}" for i in range(1, 8)}
VALID_ITEM_TYPES = {"GOAL", "COMPETENCY"}


def read_csv(path):
    """Read a CSV file and return its rows as dictionaries."""
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(f"{path.name}: missing CSV header")

        if any(not name for name in reader.fieldnames):
            raise ValueError(f"{path.name}: blank column name")

        if len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"{path.name}: duplicate column names")

        return list(reader)


def parse_date(value, field_name):
    """Convert an ISO date string to a date object."""
    try:
        return date.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        raise ValueError(
            f"Invalid date in {field_name}: {value!r}. "
            "Expected YYYY-MM-DD."
        )


def parse_integer(value, field_name):
    """Convert a string to an integer without accepting decimals."""
    try:
        value = value.strip()

        if not value or any(ch not in "-0123456789" for ch in value):
            raise ValueError

        result = int(value)

        return result
    except (ValueError, AttributeError):
        raise ValueError(
            f"Invalid integer in {field_name}: {value!r}"
        )


def validate_rating(value, field_name):
    rating = parse_integer(value, field_name)

    if rating not in range(1, 6):
        raise ValueError(
            f"{field_name} must be between 1 and 5"
        )

    return rating


def load_employees(path):
    employees = {}
    required = {
        "employee_id", "business_unit", "grade",
        "basic_salary", "joining_date", "manager_id",
        "current_role_band", "grade_start_date",
        "previous_final_rating"
    }

    for row in read_csv(path):
        missing = required - row.keys()

        if missing:
            raise ValueError(
                f"employees.csv missing columns: {sorted(missing)}"
            )

        employee_id = row["employee_id"].strip()

        if not employee_id:
            raise ValueError("Employee ID cannot be empty")

        if employee_id in employees:
            raise ValueError(f"Duplicate employee ID: {employee_id}")

        grade = row["grade"].strip().upper()

        if grade not in VALID_GRADES:
            raise ValueError(
                f"{employee_id}: invalid grade {grade!r}"
            )

        salary = parse_integer(
            row["basic_salary"], f"{employee_id}.basic_salary"
        )

        if salary <= 0:
            raise ValueError(
                f"{employee_id}: salary must be positive"
            )

        business_unit = row["business_unit"].strip()
        manager_id = row["manager_id"].strip()
        role_band = row["current_role_band"].strip()

        if not business_unit or not manager_id or not role_band:
            raise ValueError(
                f"{employee_id}: business unit, manager ID and "
                "role band are required"
            )

        joining_date = parse_date(
            row["joining_date"], f"{employee_id}.joining_date"
        )

        grade_start_date = parse_date(
            row["grade_start_date"],
            f"{employee_id}.grade_start_date"
        )

        if grade_start_date < joining_date:
            raise ValueError(
                f"{employee_id}: grade start date precedes joining date"
            )

        previous_text = row["previous_final_rating"].strip()

        previous_rating = (
            validate_rating(
                previous_text,
                f"{employee_id}.previous_final_rating"
            )
            if previous_text else None
        )

        employees[employee_id] = Employee(
            employee_id=employee_id,
            business_unit=business_unit,
            grade=grade,
            basic_salary=salary,
            joining_date=joining_date,
            manager_id=manager_id,
            current_role_band=role_band,
            grade_start_date=grade_start_date,
            previous_final_rating=previous_rating
        )

    return employees


def load_goals(path, employees):
    goals = []
    seen = set()
    required = {
        "employee_id", "goal_id", "goal_name", "weight"
    }

    for row in read_csv(path):
        missing = required - row.keys()

        if missing:
            raise ValueError(
                f"goals.csv missing columns: {sorted(missing)}"
            )

        employee_id = row["employee_id"].strip()
        goal_id = row["goal_id"].strip()
        goal_name = row["goal_name"].strip()

        if employee_id not in employees:
            raise ValueError(
                f"Goal references unknown employee: {employee_id}"
            )

        if not goal_id or not goal_name:
            raise ValueError(
                f"{employee_id}: goal ID and name are required"
            )

        key = (employee_id, goal_id)

        if key in seen:
            raise ValueError(f"Duplicate goal: {key}")

        seen.add(key)

        weight = parse_integer(
            row["weight"], f"{employee_id}.{goal_id}.weight"
        )

        if weight <= 0 or weight > 100:
            raise ValueError(
                f"{employee_id}.{goal_id}: weight must be 1–100"
            )

        goals.append(
            Goal(employee_id, goal_id, goal_name, weight)
        )

    totals = {employee_id: 0 for employee_id in employees}

    for goal in goals:
        totals[goal.employee_id] += goal.weight

    for employee_id, total in totals.items():
        if total != 100:
            raise ValueError(
                f"INVALID_WEIGHTS: {employee_id} has "
                f"goal weights totaling {total}, not 100"
            )

    return goals


def load_ratings(path, employees, goals):
    ratings = []
    seen = set()
    goal_ids = {
        (goal.employee_id, goal.goal_id) for goal in goals
    }

    required = {
        "employee_id", "item_type", "item_id",
        "self_rating", "manager_rating"
    }

    for row in read_csv(path):
        missing = required - row.keys()

        if missing:
            raise ValueError(
                f"ratings.csv missing columns: {sorted(missing)}"
            )

        employee_id = row["employee_id"].strip()
        item_type = row["item_type"].strip().upper()
        item_id = row["item_id"].strip()

        if employee_id not in employees:
            raise ValueError(
                f"Rating references unknown employee: {employee_id}"
            )

        if item_type not in VALID_ITEM_TYPES:
            raise ValueError(
                f"{employee_id}: invalid item type {item_type!r}"
            )

        if not item_id:
            raise ValueError(f"{employee_id}: item ID is required")

        if item_type == "GOAL":
            if (employee_id, item_id) not in goal_ids:
                raise ValueError(
                    f"{employee_id}: rating references unknown goal "
                    f"{item_id}"
                )

        key = (employee_id, item_type, item_id)

        if key in seen:
            raise ValueError(f"Duplicate rating: {key}")

        seen.add(key)

        self_rating = validate_rating(
            row["self_rating"], f"{employee_id}.self_rating"
        )

        manager_rating = validate_rating(
            row["manager_rating"], f"{employee_id}.manager_rating"
        )

        ratings.append(
            Rating(
                employee_id,
                item_type,
                item_id,
                self_rating,
                manager_rating
            )
        )

    # Require a rating for every registered goal.
    for employee_id, goal_id in goal_ids:
        if (employee_id, "GOAL", goal_id) not in seen:
            raise ValueError(
                f"Missing manager/self rating for goal "
                f"{employee_id}/{goal_id}"
            )

    # Require at least one competency rating per employee.
    for employee_id in employees:
        has_competency = any(
            r.employee_id == employee_id
            and r.item_type == "COMPETENCY"
            for r in ratings
        )

        if not has_competency:
            raise ValueError(
                f"{employee_id}: at least one competency rating required"
            )

    return ratings


def load_and_validate(input_dir):
    """Load all core data and validate relationships."""
    input_dir = Path(input_dir)

    employees = load_employees(input_dir / "employees.csv")
    goals = load_goals(input_dir / "goals.csv", employees)
    ratings = load_ratings(
        input_dir / "ratings.csv", employees, goals
    )

    return employees, goals, ratings