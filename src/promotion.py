from math import ceil

from src.compensation import calculate_completed_months


PROMOTION_INCREMENT_RATE = 0.05
DEFAULT_GRADE_ORDER = tuple(f"G{grade}" for grade in range(1, 8))


def next_grade_in_order(current_grade, grade_order):
    """Return the next grade in the supplied grade-band order, if any."""
    grades = tuple(grade.strip().upper() for grade in grade_order)
    if not grades or len(grades) != len(set(grades)):
        raise ValueError("Grade order must contain unique grade IDs")
    current_grade = current_grade.strip().upper()
    if current_grade not in grades:
        raise ValueError(f"Grade {current_grade!r} is not in the grade order")
    position = grades.index(current_grade)
    return grades[position + 1] if position + 1 < len(grades) else None


def check_promotion_eligibility(employee, final_rating, appraisal_date):
    """
    Check whether an employee is eligible for promotion.

    Rating 5 requires 24 months in grade.
    Rating 4 requires 36 months in grade.
    """
    months_in_grade = getattr(employee, "months_in_grade", None)
    if months_in_grade is None:
        months_in_grade = calculate_completed_months(
            employee.grade_start_date,
            appraisal_date,
        )

    if final_rating == 5 and months_in_grade >= 24:
        return True

    if final_rating == 4 and months_in_grade >= 36:
        return True

    return False


def select_promotions(
    employees,
    final_results,
    scores,
    eligibility,
    appraisal_date,
    grade_order=None,
):
    """Select promotion candidates subject to each unit's promotion cap."""
    grade_order = tuple(
        grade.strip().upper()
        for grade in (grade_order or DEFAULT_GRADE_ORDER)
    )
    if not grade_order or len(grade_order) != len(set(grade_order)):
        raise ValueError("Grade order must contain unique grade IDs")
    eligible_headcounts = {}
    candidates_by_unit = {}

    for employee_id, employee in employees.items():
        if eligibility[employee_id] != "ELIGIBLE":
            continue

        eligible_headcounts[employee.business_unit] = (
            eligible_headcounts.get(employee.business_unit, 0) + 1
        )

        employee_grade = employee.grade.strip().upper()
        if employee_grade not in grade_order:
            raise ValueError(
                f"Employee {employee_id} has grade {employee.grade!r} "
                "outside the grade order"
            )
        if employee_grade == grade_order[-1]:
            continue

        final_rating = final_results[employee_id]["final_rating"]
        if check_promotion_eligibility(
            employee, final_rating, appraisal_date
        ):
            candidates_by_unit.setdefault(
                employee.business_unit, []
            ).append(employee_id)

    selected = set()

    for business_unit, candidates in candidates_by_unit.items():
        promotion_limit = ceil(
            eligible_headcounts[business_unit] * 0.08
        )
        candidates.sort(
            key=lambda employee_id: -scores[employee_id]["raw_score"]
        )
        selected.update(candidates[:promotion_limit])

    return selected
