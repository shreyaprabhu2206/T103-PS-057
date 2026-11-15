
import csv
from datetime import date
from math import ceil, floor, isfinite
from pathlib import Path


INCREMENT_RATES = {
    5: 0.14,
    4: 0.10,
    3: 0.06,
    2: 0.02,
    1: 0.00,
}

VARIABLE_TARGET_RATES = {
    "G1": 0.15,
    "G2": 0.15,
    "G3": 0.15,
    "G4": 0.20,
    "G5": 0.20,
    "G6": 0.30,
    "G7": 0.30,
}

VARIABLE_RATING_MULTIPLIERS = {
    5: 1.5,
    4: 1.2,
    3: 1.0,
    2: 0.5,
    1: 0.0,
}


def load_company_multiplier(commands_path):
    """Read the company multiplier from a pipe-delimited command file."""
    company_multiplier = None

    with Path(commands_path).open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            parts = [part.strip() for part in line.split("|")]
            if not parts or parts[0] != "SET_COMPANY_MULTIPLIER":
                continue
            if len(parts) != 2 or not parts[1]:
                raise ValueError(
                    "SET_COMPANY_MULTIPLIER must have one numeric value "
                    f"(line {line_number})"
                )
            if company_multiplier is not None:
                raise ValueError(
                    "SET_COMPANY_MULTIPLIER may be specified only once"
                )

            try:
                company_multiplier = float(parts[1])
            except ValueError:
                raise ValueError(
                    "SET_COMPANY_MULTIPLIER must be numeric "
                    f"(line {line_number})"
                )

    if company_multiplier is None:
        raise ValueError(
            "Command file is missing SET_COMPANY_MULTIPLIER"
        )
    if not 0.8 <= company_multiplier <= 1.2:
        raise ValueError(
            "Company multiplier must be between 0.8 and 1.2"
        )

    return company_multiplier


def load_increment_budgets(path):
    """Load per-business-unit increment budgets from a CSV file."""
    budgets = {}

    with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {"business_unit", "increment_budget"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(
                "budgets.csv must contain business_unit and "
                "increment_budget columns"
            )

        for row in reader:
            business_unit = (row.get("business_unit") or "").strip()
            if not business_unit:
                raise ValueError("Business unit in budgets.csv is required")
            if business_unit in budgets:
                raise ValueError(
                    f"Duplicate budget for business unit {business_unit}"
                )

            try:
                budget = float(row["increment_budget"])
            except (TypeError, ValueError):
                raise ValueError(
                    f"{business_unit}: increment budget must be numeric"
                )
            if not isfinite(budget):
                raise ValueError(
                    f"{business_unit}: increment budget must be finite"
                )
            if budget < 0:
                raise ValueError(
                    f"{business_unit}: increment budget cannot be negative"
                )

            budgets[business_unit] = budget

    return budgets


def calculate_scaled_increment_rates(
    employees,
    final_results,
    appraisal_year,
    budgets,
    promoted_employee_ids=(),
    appraisal_cutoff_date=None,
    proration_through_cutoff=False,
    annualize_cost=False,
    grade_bands=None,
    new_grades=None,
):
    """Scale unit increment rates when estimated cost exceeds its budget."""
    new_grades = new_grades or {}
    unit_costs = {}
    unit_employee_ids = {}

    for employee_id, employee in employees.items():
        final_rating = final_results[employee_id]["final_rating"]
        if final_rating is None:
            continue

        unit = employee.business_unit
        if unit not in budgets:
            raise ValueError(f"No increment budget found for {unit}")

        on_pip = (
            final_rating == 1
            or (
                final_rating == 2
                and employee.previous_final_rating == 2
            )
        )
        rate = 0.0 if on_pip else INCREMENT_RATES[final_rating]
        if employee_id in promoted_employee_ids and not on_pip:
            rate += 0.05

        cost = (
            employee.basic_salary
            * rate
            * calculate_proration(
                employee.joining_date,
                appraisal_year,
                appraisal_cutoff_date,
                through_cutoff=proration_through_cutoff,
            )
            * (12 if annualize_cost else 1)
        )
        unit_costs[unit] = unit_costs.get(unit, 0.0) + cost
        unit_employee_ids.setdefault(unit, []).append(employee_id)

    if annualize_cost and grade_bands is not None:
        scaled_rates = {}

        def rates_at_scale(employee_ids, scale):
            rates = {}
            for employee_id in employee_ids:
                rating = final_results[employee_id]["final_rating"]
                employee = employees[employee_id]
                on_pip = (
                    rating == 1
                    or (
                        rating == 2
                        and employee.previous_final_rating == 2
                    )
                )
                if on_pip:
                    rates[employee_id] = 0.0
                    continue
                rate = INCREMENT_RATES[rating]
                if employee_id in promoted_employee_ids:
                    rate += 0.05
                rates[employee_id] = floor(rate * scale * 1000) / 1000
            return rates

        def annual_cost(employee_ids, rates):
            total = 0.0
            for employee_id in employee_ids:
                employee = employees[employee_id]
                rating = final_results[employee_id]["final_rating"]
                proration = calculate_proration(
                    employee.joining_date,
                    appraisal_year,
                    appraisal_cutoff_date,
                    through_cutoff=proration_through_cutoff,
                )
                if rates[employee_id] == 0:
                    revised_salary = employee.basic_salary
                else:
                    revised_salary = ceil(
                        (
                            employee.basic_salary
                            + employee.basic_salary * rates[employee_id] * proration
                        ) / 100
                    ) * 100
                    if rating >= 3:
                        revised_salary = max(revised_salary, 25000)
                applied_grade = new_grades.get(
                    employee_id, employee.grade
                )
                grade_band = grade_bands[applied_grade]
                revised_salary = min(
                    revised_salary, grade_band["band_max"]
                )
                total += max(
                    0.0, revised_salary - employee.basic_salary
                ) * 12
            return total

        for unit, employee_ids in unit_employee_ids.items():
            full_rate = rates_at_scale(employee_ids, 1.0)
            if annual_cost(employee_ids, full_rate) <= budgets[unit]:
                scaled_rates.update(full_rate)
                continue

            minimum_rate = rates_at_scale(employee_ids, 0.0)
            if annual_cost(employee_ids, minimum_rate) > budgets[unit]:
                raise ValueError(
                    f"{unit}: increment budget is below the unavoidable "
                    "minimum-salary-floor cost"
                )

            low, high = 0.0, 1.0
            for _ in range(32):
                middle = (low + high) / 2
                candidate_rates = rates_at_scale(employee_ids, middle)
                if annual_cost(employee_ids, candidate_rates) <= budgets[unit]:
                    low = middle
                else:
                    high = middle
            scaled_rates.update(rates_at_scale(employee_ids, low))
        return scaled_rates

    scaled_rates = {}
    for unit, employee_ids in unit_employee_ids.items():
        cost = unit_costs[unit]
        scale = min(1.0, budgets[unit] / cost) if cost else 1.0
        for employee_id in employee_ids:
            employee = employees[employee_id]
            rating = final_results[employee_id]["final_rating"]
            on_pip = (
                rating == 1
                or (
                    rating == 2
                    and employee.previous_final_rating == 2
                )
            )
            if on_pip:
                scaled_rates[employee_id] = 0.0
                continue

            rate = INCREMENT_RATES[rating]
            if employee_id in promoted_employee_ids:
                rate += 0.05
            scaled_rates[employee_id] = floor(rate * scale * 1000) / 1000

    return scaled_rates


def calculate_variable_pay(
    employee,
    final_rating,
    company_multiplier,
    *,
    on_pip=False,
    grade=None,
):
    """Calculate annual variable pay and round to the nearest rupee."""
    if final_rating not in VARIABLE_RATING_MULTIPLIERS:
        raise ValueError("Final rating must be between 1 and 5")
    if not isinstance(company_multiplier, (int, float)):
        raise ValueError("Company multiplier must be numeric")
    if not 0.8 <= company_multiplier <= 1.2:
        raise ValueError(
            "Company multiplier must be between 0.8 and 1.2"
        )

    applied_grade = (grade or employee.grade).strip().upper()
    if applied_grade not in VARIABLE_TARGET_RATES:
        raise ValueError(f"Unsupported grade for variable pay: {applied_grade}")
    if employee.basic_salary <= 0:
        raise ValueError("Basic salary must be positive")
    if on_pip:
        return 0

    payout = (
        VARIABLE_TARGET_RATES[applied_grade]
        * (12 * employee.basic_salary)
        * VARIABLE_RATING_MULTIPLIERS[final_rating]
        * company_multiplier
    )
    return floor(payout + 0.5)


def load_grade_bands(path):
    """Load and validate salary band limits from a grade-bands CSV."""
    with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        required = {"grade", "band_min", "band_max"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(
                "grade_bands.csv must contain grade, band_min, and "
                "band_max columns"
            )

        bands = {}

        for row in reader:
            grade = (row.get("grade") or "").strip().upper()
            if grade not in {f"G{i}" for i in range(1, 8)}:
                raise ValueError(f"Invalid grade in grade_bands.csv: {grade!r}")
            if grade in bands:
                raise ValueError(f"Duplicate grade band: {grade}")

            try:
                band_min = float(row["band_min"].strip())
                band_max = float(row["band_max"].strip())
            except (AttributeError, TypeError, ValueError):
                raise ValueError(
                    f"{grade}: band_min and band_max must be numeric"
                )

            if (
                not isfinite(band_min)
                or not isfinite(band_max)
                or band_min <= 0
                or band_max < band_min
            ):
                raise ValueError(f"{grade}: invalid salary band limits")

            bands[grade] = {
                "band_min": band_min,
                "band_max": band_max,
            }

    expected_grades = {f"G{i}" for i in range(1, 8)}
    missing_grades = expected_grades - bands.keys()
    if missing_grades:
        raise ValueError(
            "grade_bands.csv is missing grades: "
            f"{', '.join(sorted(missing_grades))}"
        )

    return bands


def calculate_completed_months(start_date, end_date):
    """Calculate completed months between two dates."""

    months = (
        (end_date.year - start_date.year) * 12
        + end_date.month - start_date.month
    )

    if end_date.day < start_date.day:
        months -= 1

    return max(0, months)


def calculate_proration(
    joining_date,
    appraisal_year,
    appraisal_cutoff_date=None,
    *,
    through_cutoff=False,
):
    """
    Calculate increment proration for the appraisal cycle.

    Assumption: the cycle runs from 1 April of appraisal_year
    to 31 March of the following year.
    """

    cycle_start = date(appraisal_year, 4, 1)
    cycle_end = date(appraisal_year + 1, 3, 31)
    cutoff_date = appraisal_cutoff_date or date(appraisal_year, 9, 30)

    if joining_date <= cycle_start:
        return 1.0

    if joining_date > cutoff_date:
        return 0.0

    proration_end = cutoff_date if through_cutoff else cycle_end
    if through_cutoff and joining_date == cutoff_date:
        completed_months = (
            cutoff_date.year - cycle_start.year
        ) * 12 + cutoff_date.month - cycle_start.month + 1
    else:
        completed_months = calculate_completed_months(
            joining_date, proration_end
        )

    return completed_months / 12


def calculate_compensation(
    employee,
    final_rating,
    appraisal_year,
    *,
    grade_bands_path=None,
    new_grade=None,
    is_promotion=False,
    company_multiplier=1.0,
    increment_rate_override=None,
    appraisal_cutoff_date=None,
    proration_through_cutoff=False,
):
    """Calculate increment and revised basic salary."""

    if final_rating not in INCREMENT_RATES:
        raise ValueError("Final rating must be between 1 and 5")

    if final_rating is None:
        raise ValueError("Employee must have a final rating")

    if employee.basic_salary <= 0:
        raise ValueError("Basic salary must be positive")

    if new_grade is not None and grade_bands_path is None:
        raise ValueError(
            "A grade_bands_path is required when applying a promoted grade"
        )

    on_pip = (
        final_rating == 1
        or (
            final_rating == 2
            and employee.previous_final_rating == 2
        )
    )
    if (
        increment_rate_override is not None
        and increment_rate_override < 0
    ):
        raise ValueError("Increment rate override cannot be negative")

    if increment_rate_override is None:
        increment_rate = (
            0.0 if on_pip else INCREMENT_RATES[final_rating]
        )
        promotion_increment_rate = (
            0.05 if is_promotion and not on_pip else 0.0
        )
        increment_rate += promotion_increment_rate
    else:
        increment_rate = 0.0 if on_pip else increment_rate_override
        base_plus_promotion_rate = (
            INCREMENT_RATES[final_rating] + 0.05
        )
        promotion_increment_rate = (
            0.05 * increment_rate / base_plus_promotion_rate
            if is_promotion and not on_pip
            else 0.0
        )

    proration = calculate_proration(
        employee.joining_date,
        appraisal_year,
        appraisal_cutoff_date,
        through_cutoff=proration_through_cutoff,
    )

    increment_amount = employee.basic_salary * increment_rate * proration

    revised_salary = (
        employee.basic_salary
        if on_pip
        else employee.basic_salary + increment_amount
    )

    if not on_pip:
        # Round revised salary up to the next ₹100.
        revised_salary = ceil(revised_salary / 100) * 100

    if not on_pip and final_rating >= 3 and revised_salary < 25000:
        revised_salary = 25000

    applied_grade = (new_grade or employee.grade).strip().upper()
    grade_band_max = None
    lump_sum = 0

    if grade_bands_path is not None:
        grade_bands = load_grade_bands(grade_bands_path)
        if applied_grade not in grade_bands:
            raise ValueError(
                f"No salary band found for grade {applied_grade!r}"
            )

        grade_band_max = grade_bands[applied_grade]["band_max"]
        lump_sum = max(0, revised_salary - grade_band_max)
        revised_salary = min(revised_salary, grade_band_max)

    variable_pay = calculate_variable_pay(
        employee,
        final_rating,
        company_multiplier,
        on_pip=on_pip,
        grade=applied_grade,
    )

    return {
        "employee_id": employee.employee_id,
        "final_rating": final_rating,
        "on_pip": on_pip,
        "increment_rate": increment_rate,
        "promotion_increment_rate": promotion_increment_rate,
        "proration": proration,
        "increment_amount": round(increment_amount, 2),
        "current_salary": employee.basic_salary,
        "revised_salary": revised_salary,
        "grade": applied_grade,
        "grade_band_max": grade_band_max,
        "lump_sum": lump_sum,
        "variable_pay": variable_pay,
    }
