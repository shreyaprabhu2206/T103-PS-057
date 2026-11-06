
import unittest
from datetime import date

from src.models import Employee, Goal, Rating
from src.scoring import calculate_raw_scores


class TestScoring(unittest.TestCase):

    def setUp(self):
        self.employees = {
            "E001": Employee(
                employee_id="E001",
                business_unit="IT",
                grade="G3",
                basic_salary=30000,
                joining_date=date(2023, 6, 15),
                manager_id="M001",
                current_role_band="G3",
                grade_start_date=date(2022, 6, 15),
                previous_final_rating=3
            )
        }

        self.goals = [
            Goal(
                employee_id="E001",
                goal_id="G01",
                goal_name="Complete project",
                weight=60
            ),
            Goal(
                employee_id="E001",
                goal_id="G02",
                goal_name="Improve productivity",
                weight=40
            )
        ]

        self.ratings = [
            Rating("E001", "GOAL", "G01", 4, 5),
            Rating("E001", "GOAL", "G02", 3, 4),
            Rating("E001", "COMPETENCY", "C01", 4, 4),
            Rating("E001", "COMPETENCY", "C02", 3, 5)
        ]

    def test_goal_score(self):
        result = calculate_raw_scores(
            self.employees, self.goals, self.ratings
        )
        self.assertAlmostEqual(result["E001"]["goal_score"], 4.6)

    def test_competency_score(self):
        result = calculate_raw_scores(
            self.employees, self.goals, self.ratings
        )
        self.assertAlmostEqual(
            result["E001"]["competency_score"], 4.5
        )

    def test_raw_score(self):
        result = calculate_raw_scores(
            self.employees, self.goals, self.ratings
        )
        self.assertAlmostEqual(result["E001"]["raw_score"], 4.57)

    def test_missing_competency_ratings(self):
        ratings_without_competencies = [
            rating for rating in self.ratings
            if rating.item_type != "COMPETENCY"
        ]

        with self.assertRaises(ValueError):
            calculate_raw_scores(
                self.employees,
                self.goals,
                ratings_without_competencies
            )


if __name__ == "__main__":
    unittest.main()
