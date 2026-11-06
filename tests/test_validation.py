
import unittest
import csv
import tempfile

from pathlib import Path
from datetime import date

from src.models import Employee, Goal
from src.validation import (
    parse_date,
    parse_integer,
    validate_rating,
    load_goals,
    load_ratings,
)


class TestValidation(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)

        self.employees = {
            "E001": Employee(
                employee_id="E001",
                business_unit="IT",
                grade="G3",
                basic_salary=30000,
                joining_date=date(2023, 6, 15),
                manager_id="M001",
                current_role_band="B3",
                grade_start_date=date(2023, 1, 1),
                previous_final_rating=3
            )
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_csv(self, filename, headers, rows):
        path = self.folder / filename

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        return path

    def test_valid_integer(self):
        self.assertEqual(parse_integer("25", "test"), 25)

    def test_invalid_integer(self):
        with self.assertRaises(ValueError):
            parse_integer("2.5", "test")

    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            parse_date("15-06-2023", "joining_date")

    def test_rating_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_rating("6", "manager_rating")

    def test_goal_weights_not_equal_to_100(self):
        path = self.write_csv(
            "goals.csv",
            ["employee_id", "goal_id", "goal_name", "weight"],
            [
                {
                    "employee_id": "E001",
                    "goal_id": "G01",
                    "goal_name": "Complete project",
                    "weight": "50"
                },
                {
                    "employee_id": "E001",
                    "goal_id": "G02",
                    "goal_name": "Improve productivity",
                    "weight": "40"
                }
            ]
        )

        with self.assertRaisesRegex(ValueError, "INVALID_WEIGHTS"):
            load_goals(path, self.employees)

    def test_goal_references_unknown_employee(self):
        path = self.write_csv(
            "goals.csv",
            ["employee_id", "goal_id", "goal_name", "weight"],
            [{
                "employee_id": "E999",
                "goal_id": "G01",
                "goal_name": "Complete project",
                "weight": "100"
            }]
        )

        with self.assertRaisesRegex(ValueError, "unknown employee"):
            load_goals(path, self.employees)

    def test_invalid_manager_rating(self):
        goals = [
            Goal("E001", "G01", "Complete project", 100)
        ]

        path = self.write_csv(
            "ratings.csv",
            [
                "employee_id", "item_type", "item_id",
                "self_rating", "manager_rating"
            ],
            [
                {
                    "employee_id": "E001",
                    "item_type": "GOAL",
                    "item_id": "G01",
                    "self_rating": "4",
                    "manager_rating": "7"
                }
            ]
        )

        with self.assertRaises(ValueError):
            load_ratings(path, self.employees, goals)

    def test_missing_competency_rating(self):
        goals = [
            Goal("E001", "G01", "Complete project", 100)
        ]

        path = self.write_csv(
            "ratings.csv",
            [
                "employee_id", "item_type", "item_id",
                "self_rating", "manager_rating"
            ],
            [
                {
                    "employee_id": "E001",
                    "item_type": "GOAL",
                    "item_id": "G01",
                    "self_rating": "4",
                    "manager_rating": "5"
                }
            ]
        )

        with self.assertRaisesRegex(ValueError, "competency"):
            load_ratings(path, self.employees, goals)


if __name__ == "__main__":
    unittest.main()
