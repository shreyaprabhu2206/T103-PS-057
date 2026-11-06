
from datetime import date
from math import ceil


INCREMENT_RATES = {
    5: 0.14,
    4: 0.10,
    3: 0.06,
    2: 0.02,
    1: 0.00,
}


def calculate_completed_months(start_date, end_date):
    """Calculate completed months between two dates."""

    months = (
        (end_date.year - start_date.year) * 12
        + end_date.month - start_date.month
    )

    if end_date.day < start_date.day:
        months -= 1

    return max(0, months)


def calculate_proration(joining_date, appraisal_year):
    """
    Calculate increment proration for the appraisal cycle.

    Assumption: the cycle runs from 1 April of appraisal_year
    to 31 March of the following year.
    """

    cycle_start = date(appraisal_year, 4, 1)
    cycle_end = date(appraisal_year + 1, 3, 31)

    if joining_date <= cycle_start:
        return 1.0

    if joining_date > date(appraisal_year, 9, 30):
        return 0.0

    completed_months = calculate_completed_months(
        joining_date, cycle_end
    )

    return completed_months / 12


def calculate_compensation(employee, final_rating, appraisal_year):
    """Calculate increment and revised basic salary."""

    if final_rating not in INCREMENT_RATES:
        raise ValueError("Final rating must be between 1 and 5")

    if final_rating is None:
        raise ValueError("Employee must have a final rating")

    if employee.basic_salary <= 0:
        raise ValueError("Basic salary must be positive")

    increment_rate = INCREMENT_RATES[final_rating]

    proration = calculate_proration(
        employee.joining_date,
        appraisal_year
    )

    increment_amount = (
        employee.basic_salary * increment_rate * proration
    )

    revised_salary = employee.basic_salary + increment_amount

    # Round revised salary up to the next ₹100.
    revised_salary = ceil(revised_salary / 100) * 100

    return {
        "employee_id": employee.employee_id,
        "final_rating": final_rating,
        "increment_rate": increment_rate,
        "proration": proration,
        "increment_amount": round(increment_amount, 2),
        "current_salary": employee.basic_salary,
        "revised_salary": revised_salary,
    }
