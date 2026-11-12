from math import ceil

from src.compensation import calculate_completed_months


PROMOTION_INCREMENT_RATE = 0.05


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
):
    """Select promotion candidates subject to each unit's promotion cap."""
    eligible_headcounts = {}
    candidates_by_unit = {}

    for employee_id, employee in employees.items():
        if eligibility[employee_id] != "ELIGIBLE":
            continue

        eligible_headcounts[employee.business_unit] = (
            eligible_headcounts.get(employee.business_unit, 0) + 1
        )

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
