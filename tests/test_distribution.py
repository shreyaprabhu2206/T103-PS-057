
import unittest
from datetime import date

from src.models import Employee
from src.calibration import (
    build_distribution_pools,
    distribute_ratings,
)


class TestDistribution(unittest.TestCase):

    def create_employee(self, employee_id, unit, joining_date):
        return Employee(
            employee_id=employee_id,
            business_unit=unit,
            grade="G3",
            basic_salary=30000,
            joining_date=joining_date,
            manager_id="M001",
            current_role_band="B3",
            grade_start_date=date(2023, 1, 1),
            previous_final_rating=3
        )

    def test_rating_distribution_for_20_employees(self):
        employees = {}
        scores = {}
        eligibility = {}

        for i in range(1, 21):
            employee_id = f"E{i:03d}"

            employees[employee_id] = self.create_employee(
                employee_id,
                "IT",
                date(2022, 1, 1)
            )

            scores[employee_id] = {
                "raw_score": float(21 - i),
                "goal_score": float(21 - i)
            }

            eligibility[employee_id] = "ELIGIBLE"

        results = distribute_ratings(
            employees, scores, eligibility, 2025
        )

        rating_counts = {
            rating: sum(
                1 for result in results.values()
                if result["final_rating"] == rating
            )
            for rating in [5, 4, 3, 2, 1]
        }

        self.assertEqual(
            rating_counts,
            {5: 2, 4: 4, 3: 10, 2: 3, 1: 1}
        )

    def test_ranking_tie_breakers(self):
        employees = {
            "E003": self.create_employee(
                "E003", "IT", date(2020, 1, 1)
            ),
            "E001": self.create_employee(
                "E001", "IT", date(2020, 1, 1)
            ),
            "E002": self.create_employee(
                "E002", "IT", date(2021, 1, 1)
            ),
            "E004": self.create_employee(
                "E004", "IT", date(2022, 1, 1)
            )
        }

        scores = {
            employee_id: {
                "raw_score": 4.0,
                "goal_score": 4.0
            }
            for employee_id in employees
        }

        eligibility = {
            employee_id: "ELIGIBLE"
            for employee_id in employees
        }

        results = distribute_ratings(
            employees, scores, eligibility, 2025
        )

        ranked_ids = sorted(
            results,
            key=lambda employee_id: results[employee_id]["rank"]
        )

        self.assertEqual(
            ranked_ids,
            ["E001", "E003", "E002", "E004"]
        )

    def test_small_business_units_are_pooled(self):
        employees = {}
        eligibility = {}

        for i in range(1, 7):
            employee_id = f"F{i:03d}"
            employees[employee_id] = self.create_employee(
                employee_id, "Finance", date(2022, 1, 1)
            )
            eligibility[employee_id] = "ELIGIBLE"

        for i in range(1, 6):
            employee_id = f"I{i:03d}"
            employees[employee_id] = self.create_employee(
                employee_id, "IT", date(2022, 1, 1)
            )
            eligibility[employee_id] = "ELIGIBLE"

        pools, units = build_distribution_pools(
            employees, eligibility
        )

        self.assertEqual(pools, [["Finance", "IT"]])


if __name__ == "__main__":
    unittest.main()
