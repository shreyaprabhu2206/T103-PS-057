import unittest
from datetime import date

from src.appeals import process_appeal
from src.calibration import distribute_ratings
from src.models import Employee, Goal, Rating
from src.scoring import calculate_raw_scores


class TestAppeals(unittest.TestCase):

    def test_appeal_recalibrates_unit_and_reports_rating_changes(self):
        employees = {}
        goals = []
        ratings = []

        for employee_id in (
            "A001", "Z001", "E003", "E004", "E005",
            "E006", "E007", "E008", "E009", "E010",
        ):
            employees[employee_id] = Employee(
                employee_id=employee_id,
                business_unit="IT",
                grade="G3",
                basic_salary=30000,
                joining_date=date(2020, 1, 1),
                manager_id="M001",
                current_role_band="B3",
                grade_start_date=date(2020, 1, 1),
            )
            goal_rating = 4 if employee_id == "A001" else (
                5 if employee_id == "Z001" else 3
            )
            goal_id = f"G-{employee_id}"
            goals.append(Goal(employee_id, goal_id, "Goal", 100))
            ratings.extend([
                Rating(employee_id, "GOAL", goal_id, 3, goal_rating),
                Rating(employee_id, "COMPETENCY", "C1", 3, 3),
            ])

        eligibility = {
            employee_id: "ELIGIBLE" for employee_id in employees
        }
        scores = calculate_raw_scores(employees, goals, ratings)
        final_results = distribute_ratings(
            employees, scores, eligibility, 2025
        )
        self.assertEqual(final_results["A001"]["final_rating"], 4)
        self.assertEqual(final_results["Z001"]["final_rating"], 5)

        scores, final_results, changed_ids = process_appeal(
            employees,
            goals,
            ratings,
            scores,
            final_results,
            eligibility,
            "A001",
            ["G-A001"],
            2025,
        )

        self.assertEqual(changed_ids, {"A001", "Z001"})
        self.assertEqual(final_results["A001"]["final_rating"], 5)
        self.assertEqual(final_results["Z001"]["final_rating"], 4)
        self.assertEqual(scores["A001"]["goal_score"], 5.0)
        self.assertEqual(scores["A001"]["raw_score"], 4.4)

    def test_appeal_rejects_more_than_two_goals(self):
        employee = Employee(
            "E001", "IT", "G3", 30000, date(2020, 1, 1), "M001",
            "B3", date(2020, 1, 1),
        )
        employees = {"E001": employee}
        goals = [
            Goal("E001", f"G{i}", "Goal", 100 // 3)
            for i in range(1, 4)
        ]
        ratings = [
            Rating("E001", "GOAL", f"G{i}", 3, 3)
            for i in range(1, 4)
        ]

        with self.assertRaisesRegex(ValueError, "one or two"):
            process_appeal(
                employees,
                goals,
                ratings,
                {},
                {},
                {"E001": "ELIGIBLE"},
                "E001",
                ["G1", "G2", "G3"],
                2025,
            )


if __name__ == "__main__":
    unittest.main()
