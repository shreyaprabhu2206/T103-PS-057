
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
        for i in range(5, 11):
            employee_id = f"E{i:03d}"
            employees[employee_id] = self.create_employee(
                employee_id, "IT", date(2023, 1, 1)
            )

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
            ["E001", "E003", "E002", "E004", "E005", "E006", "E007",
             "E008", "E009", "E010"]
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

    def test_exactly_ten_eligible_employees_are_not_pooled(self):
        employees = {
            f"E{i:03d}": self.create_employee(
                f"E{i:03d}", "IT", date(2022, 1, 1)
            )
            for i in range(10)
        }
        eligibility = {
            employee_id: "ELIGIBLE" for employee_id in employees
        }

        pools, units = build_distribution_pools(employees, eligibility)

        self.assertEqual(pools, [["IT"]])
        self.assertEqual(len(units["IT"]), 10)

    def test_nine_eligible_employees_pool_with_next_unit(self):
        employees = {
            f"A{i:03d}": self.create_employee(
                f"A{i:03d}", "Alpha", date(2022, 1, 1)
            )
            for i in range(9)
        }
        employees["B001"] = self.create_employee(
            "B001", "Beta", date(2022, 1, 1)
        )
        eligibility = {
            employee_id: "ELIGIBLE" for employee_id in employees
        }

        pools, units = build_distribution_pools(employees, eligibility)

        self.assertEqual(pools, [["Alpha", "Beta"]])
        self.assertEqual(len(units["Alpha"]) + len(units["Beta"]), 10)

    def test_identical_scores_and_tenure_use_lower_employee_id(self):
        employees = {
            employee_id: self.create_employee(
                employee_id, "IT", date(2022, 1, 1)
            )
            for employee_id in ("E002", "E001")
        }
        for i in range(3, 11):
            employee_id = f"E{i:03d}"
            employees[employee_id] = self.create_employee(
                employee_id, "IT", date(2023, 1, 1)
            )
        scores = {
            employee_id: {
                "raw_score": 4.0 if employee_id in {"E001", "E002"} else 3.0,
                "goal_score": 4.0 if employee_id in {"E001", "E002"} else 3.0,
            }
            for employee_id in employees
        }
        eligibility = {
            employee_id: "ELIGIBLE" for employee_id in employees
        }

        results = distribute_ratings(
            employees, scores, eligibility, 2025
        )

        self.assertLess(results["E001"]["rank"], results["E002"]["rank"])

    def test_fractional_bucket_remainders_are_added_to_rating_three(self):
        employees = {
            f"E{i:03d}": self.create_employee(
                f"E{i:03d}", "IT", date(2022, 1, 1)
            )
            for i in range(1, 12)
        }
        scores = {
            employee_id: {
                "raw_score": float(12 - index),
                "goal_score": float(12 - index),
            }
            for index, employee_id in enumerate(employees, start=1)
        }
        eligibility = {
            employee_id: "ELIGIBLE" for employee_id in employees
        }

        results = distribute_ratings(
            employees, scores, eligibility, 2025
        )
        rating_counts = {
            rating: sum(
                result["final_rating"] == rating
                for result in results.values()
            )
            for rating in (5, 4, 3, 2, 1)
        }
        self.assertEqual(rating_counts, {5: 1, 4: 2, 3: 7, 2: 1, 1: 0})

    def test_ineligible_employees_receive_no_distribution_rating(self):
        employees = {
            f"E{i:03d}": self.create_employee(
                f"E{i:03d}", "IT", date(2022, 1, 1)
            )
            for i in range(10)
        }
        employees["E999"] = self.create_employee(
            "E999", "IT", date(2026, 10, 1)
        )
        scores = {
            employee_id: {"raw_score": 4.0, "goal_score": 4.0}
            for employee_id in employees
            if employee_id != "E999"
        }
        eligibility = {
            employee_id: (
                "NOT_ELIGIBLE" if employee_id == "E999" else "ELIGIBLE"
            )
            for employee_id in employees
        }
        results = distribute_ratings(
            employees, scores, eligibility, 2025
        )
        self.assertIsNone(results["E999"]["final_rating"])
        self.assertEqual(
            sum(result["final_rating"] is not None for result in results.values()),
            10,
        )

    def test_final_residual_pool_sizes_one_five_and_nine(self):
        expected_counts = {
            1: {5: 0, 4: 0, 3: 1, 2: 0, 1: 0},
            5: {5: 0, 4: 1, 3: 4, 2: 0, 1: 0},
            9: {5: 0, 4: 1, 3: 7, 2: 1, 1: 0},
        }
        for count, expected in expected_counts.items():
            with self.subTest(count=count):
                employees = {
                    f"E{i:03d}": self.create_employee(
                        f"E{i:03d}", "ZETA", date(2022, 1, 1)
                    )
                    for i in range(count)
                }
                scores = {
                    employee_id: {
                        "raw_score": float(count - index),
                        "goal_score": float(count - index),
                    }
                    for index, employee_id in enumerate(employees)
                }
                eligibility = {
                    employee_id: "ELIGIBLE" for employee_id in employees
                }

                pools, _ = build_distribution_pools(employees, eligibility)
                results = distribute_ratings(
                    employees, scores, eligibility, 2025
                )
                actual = {
                    rating: sum(
                        result["final_rating"] == rating
                        for result in results.values()
                    )
                    for rating in (5, 4, 3, 2, 1)
                }
                self.assertEqual(pools, [["ZETA"]])
                self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
