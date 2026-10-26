
from datetime import date


def check_eligibility(employee, appraisal_year):
    """
    Determine eligibility for the appraisal cycle.

    Employees who join after 30 September are excluded.
    """
    cutoff_date = date(appraisal_year, 9, 30)

    if employee.joining_date > cutoff_date:
        return "NOT_ELIGIBLE"

    return "ELIGIBLE"


def get_eligibility_results(employees, appraisal_year):
    """Return eligibility status for every employee."""
    results = {}

    for employee_id, employee in employees.items():
        results[employee_id] = check_eligibility(
            employee, appraisal_year
        )

    return results

import math


def build_distribution_pools(employees, eligibility):
    """Pool small business units before rating distribution."""

    units = {}

    for employee_id, employee in employees.items():
        if eligibility[employee_id] != "ELIGIBLE":
            continue

        units.setdefault(employee.business_unit, []).append(
            employee_id
        )

    unit_names = sorted(units)
    pools = []
    i = 0

    while i < len(unit_names):
        unit = unit_names[i]

        if len(units[unit]) >= 10:
            pools.append([unit])
            i += 1
            continue

        # A small unit is combined with the next alphabetical unit(s)
        group = [unit]
        count = len(units[unit])
        i += 1

        while count < 10 and i < len(unit_names):
            next_unit = unit_names[i]
            group.append(next_unit)
            count += len(units[next_unit])
            i += 1

        pools.append(group)

    # If the final pool is still below 10, merge it with
    # the preceding pool because no next alphabetical unit exists.
    if len(pools) > 1:
        last_pool = pools[-1]
        last_count = sum(len(units[u]) for u in last_pool)

        if last_count < 10:
            pools[-2].extend(last_pool)
            pools.pop()

    return pools, units


def distribute_ratings(employees, scores, eligibility, appraisal_year):
    """Assign forced-distribution ratings to eligible employees."""

    pools, units = build_distribution_pools(employees, eligibility)
    results = {}

    for group in pools:
        employee_ids = []

        for unit in group:
            employee_ids.extend(units[unit])

        # Best raw score first, then goal score, longer tenure,
        # and finally lower employee ID.
        employee_ids.sort(
            key=lambda employee_id: (
                -scores[employee_id]["raw_score"],
                -scores[employee_id]["goal_score"],
                employees[employee_id].joining_date,
                employee_id,
            )
        )

        n = len(employee_ids)

        bucket_sizes = {
            5: math.floor(n * 0.10),
            4: math.floor(n * 0.20),
            3: math.floor(n * 0.50),
            2: math.floor(n * 0.15),
            1: math.floor(n * 0.05),
        }

        assigned = sum(bucket_sizes.values())
        bucket_sizes[3] += n - assigned

        pool_name = " + ".join(group)
        position = 0

        for rating in [5, 4, 3, 2, 1]:
            size = bucket_sizes[rating]

            for _ in range(size):
                employee_id = employee_ids[position]

                results[employee_id] = {
                    "final_rating": rating,
                    "pool": pool_name,
                    "rank": position + 1,
                }

                position += 1

    # Employees excluded by the eligibility cutoff receive no rating.
    for employee_id, status in eligibility.items():
        if status != "ELIGIBLE":
            results[employee_id] = {
                "final_rating": None,
                "pool": None,
                "rank": None,
            }

    return results
