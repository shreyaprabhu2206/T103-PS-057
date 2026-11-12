import csv
from pathlib import Path

from src.calibration import build_distribution_pools


LETTERS_COLUMNS = [
    "emp_id", "unit", "eligible", "raw_score", "goal_score",
    "final_rating", "increment_pct", "pro_rated", "revised_basic",
    "lump_sum", "variable_payout", "promoted", "new_grade", "pip",
    "status_code",
]

DISTRIBUTION_COLUMNS = [
    "print_no", "unit_or_pool", "eligible_count", "rating",
    "bucket_size", "emp_ids",
]

APPEAL_CHANGES_COLUMNS = [
    "appeal_id", "unit_or_pool", "emp_id", "rating_before", "rating_after",
]


def _pool_name(units):
    return "+".join(units)


def distribution_rows(
    employees, eligibility, final_results, print_no
):
    """Create one row per pool/rating for a distribution snapshot."""
    pools, unit_members = build_distribution_pools(employees, eligibility)
    rows = []

    for units in pools:
        employee_ids = [
            employee_id
            for unit in units
            for employee_id in unit_members[unit]
        ]
        pool_name = _pool_name(units)
        for rating in (5, 4, 3, 2, 1):
            rated_ids = [
                employee_id for employee_id in employee_ids
                if final_results[employee_id]["final_rating"] == rating
            ]
            rated_ids.sort(
                key=lambda employee_id: final_results[employee_id]["rank"]
            )
            rows.append({
                "print_no": print_no,
                "unit_or_pool": pool_name,
                "eligible_count": len(employee_ids),
                "rating": rating,
                "bucket_size": len(rated_ids),
                "emp_ids": ",".join(rated_ids),
            })

    return rows


def write_csv(path, columns, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_letters(path, rows):
    write_csv(path, LETTERS_COLUMNS, rows)


def write_distribution(path, rows):
    write_csv(path, DISTRIBUTION_COLUMNS, rows)


def write_appeal_changes(path, rows):
    write_csv(path, APPEAL_CHANGES_COLUMNS, rows)