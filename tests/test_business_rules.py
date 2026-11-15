import csv
import json
import tempfile
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path

from src.official_data import load_official_data


class TestOfficialInputBusinessRules(unittest.TestCase):
    employee_columns = [
        "emp_id", "name", "unit", "grade", "basic_salary",
        "date_of_joining", "manager_id", "months_in_grade",
        "previous_year_rating", "role_band",
    ]
    goal_columns = ["emp_id", "goal_id", "goal_title", "weight"]
    rating_columns = [
        "emp_id", "item_type", "item_id", "self_rating", "manager_rating",
    ]
    base_employee = {
        "emp_id": "EMP-0001",
        "name": "Employee One",
        "unit": "ENGINEERING",
        "grade": "G3",
        "basic_salary": "30000.00",
        "date_of_joining": "2020-01-01",
        "manager_id": "M001",
        "months_in_grade": "36",
        "previous_year_rating": "3",
        "role_band": "IC",
    }

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_csv(self, filename, columns, rows):
        path = self.folder / filename
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _load(
        self,
        employees=None,
        goals=None,
        ratings=None,
        catalog=None,
        band_min="18000",
        band_max="60000",
        unit_budget="500000",
        employee_columns=None,
    ):
        employees = employees or [dict(self.base_employee)]
        goals = goals or [
            {
                "emp_id": "EMP-0001",
                "goal_id": "G1",
                "goal_title": "Goal",
                "weight": "100",
            }
        ]
        ratings = ratings or [
            {
                "emp_id": "EMP-0001",
                "item_type": "GOAL",
                "item_id": "G1",
                "self_rating": "3",
                "manager_rating": "4",
            },
            {
                "emp_id": "EMP-0001",
                "item_type": "COMPETENCY",
                "item_id": "C1",
                "self_rating": "3",
                "manager_rating": "4",
            },
        ]
        employee_path = self._write_csv(
            "employees.csv",
            employee_columns or self.employee_columns,
            employees,
        )
        goals_path = self._write_csv("goals.csv", self.goal_columns, goals)
        ratings_path = self._write_csv(
            "ratings.csv", self.rating_columns, ratings
        )
        bands_path = self._write_csv(
            "grade_bands.csv",
            ["grade", "band_min", "band_max"],
            [
                {
                    "grade": f"G{grade}",
                    "band_min": band_min,
                    "band_max": band_max,
                }
                for grade in range(1, 8)
            ],
        )
        units_path = self._write_csv(
            "units.csv",
            ["unit", "increment_budget_annual", "unit_head"],
            [
                {
                    "unit": unit,
                    "increment_budget_annual": unit_budget,
                    "unit_head": "M001",
                }
                for unit in sorted({row["unit"] for row in employees})
            ],
        )
        catalog_path = self.folder / "competency_catalog.json"
        catalog_path.write_text(
            json.dumps(catalog or {
                "status": "PROVISIONAL",
                "provenance": "Test fixture",
                "competency_ids": ["C1"],
                "default_required_competencies": ["C1"],
                "employee_required_competencies": {},
            }),
            encoding="utf-8",
        )
        return load_official_data(
            employee_path,
            goals_path,
            ratings_path,
            bands_path,
            units_path,
            date(2026, 9, 30),
            competency_catalog_path=catalog_path,
        )

    def test_br01_duplicate_employee_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate employee ID"):
            self._load(
                employees=[
                    dict(self.base_employee),
                    dict(self.base_employee),
                ]
            )

    def test_br02_required_fields_and_official_enums_are_validated(self):
        for field in ("name", "unit", "manager_id", "role_band"):
            with self.subTest(field=field):
                employee = dict(self.base_employee)
                employee[field] = ""
                with self.assertRaisesRegex(ValueError, "are required"):
                    self._load(employees=[employee])

        for field, value in (("unit", "UNKNOWN"), ("role_band", "BAND")):
            with self.subTest(field=field):
                employee = dict(self.base_employee)
                employee[field] = value
                with self.assertRaisesRegex(ValueError, "invalid"):
                    self._load(employees=[employee])

        employee = dict(self.base_employee, date_of_joining="")
        with self.assertRaisesRegex(ValueError, "invalid date_of_joining"):
            self._load(employees=[employee])

    def test_br03_only_supported_grades_are_accepted(self):
        employee = dict(self.base_employee, grade="G8")
        with self.assertRaisesRegex(ValueError, "invalid grade"):
            self._load(employees=[employee])

    def test_br04_basic_salary_must_be_positive(self):
        for salary in ("0", "-1", "nan", "inf", "-inf"):
            with self.subTest(salary=salary):
                employee = dict(self.base_employee, basic_salary=salary)
                with self.assertRaisesRegex(ValueError, "must be positive"):
                    self._load(employees=[employee])

    def test_br05_goal_weights_must_total_100(self):
        employees = [
            dict(self.base_employee),
            dict(self.base_employee, emp_id="EMP-0002"),
        ]
        goals = [
            {"emp_id": "EMP-0001", "goal_id": "G1", "goal_title": "A", "weight": "99"},
            {"emp_id": "EMP-0002", "goal_id": "G1", "goal_title": "B", "weight": "50"},
            {"emp_id": "EMP-0002", "goal_id": "G2", "goal_title": "C", "weight": "51"},
        ]
        ratings = []
        for employee_id, goal_id in (
            ("EMP-0001", "G1"),
            ("EMP-0002", "G1"),
            ("EMP-0002", "G2"),
        ):
            ratings.append({
                "emp_id": employee_id,
                "item_type": "GOAL",
                "item_id": goal_id,
                "self_rating": "3",
                "manager_rating": "4",
            })
        ratings.extend(
            {
                "emp_id": employee_id,
                "item_type": "COMPETENCY",
                "item_id": "C1",
                "self_rating": "3",
                "manager_rating": "4",
            }
            for employee_id in ("EMP-0001", "EMP-0002")
        )

        loaded = self._load(employees, goals, ratings)
        self.assertEqual(loaded[3], {
            "EMP-0001": "INVALID_WEIGHTS",
            "EMP-0002": "INVALID_WEIGHTS",
        })

    def test_missing_goal_title_is_rejected(self):
        goals = [{
            "emp_id": "EMP-0001",
            "goal_id": "G1",
            "goal_title": "",
            "weight": "100",
        }]
        with self.assertRaisesRegex(ValueError, "Invalid or duplicate goal"):
            self._load(goals=goals)

    def test_blank_csv_header_name_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError, "employees.csv has a blank column name"
        ):
            self._load(employee_columns=[*self.employee_columns, ""])

    def test_duplicate_csv_header_name_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError, "employees.csv has duplicate column names"
        ):
            self._load(
                employee_columns=[*self.employee_columns, "emp_id"]
            )

    def test_non_finite_grade_bands_and_unit_budgets_are_rejected(self):
        for value in ("nan", "inf", "-inf"):
            with self.subTest(field="band_min", value=value):
                with self.assertRaisesRegex(
                    ValueError, "invalid salary band limits"
                ):
                    self._load(band_min=value)
            with self.subTest(field="band_max", value=value):
                with self.assertRaisesRegex(
                    ValueError, "invalid salary band limits"
                ):
                    self._load(band_max=value)
            with self.subTest(field="unit_budget", value=value):
                with self.assertRaisesRegex(ValueError, "must be finite"):
                    self._load(unit_budget=value)

    def test_br06_self_and_manager_ratings_must_be_between_one_and_five(self):
        for field, value in (
            ("self_rating", "0"),
            ("self_rating", "6"),
            ("manager_rating", "0"),
            ("manager_rating", "6"),
            ("manager_rating", ""),
        ):
            with self.subTest(field=field, value=value):
                ratings = [
                    {
                        "emp_id": "EMP-0001",
                        "item_type": "GOAL",
                        "item_id": "G1",
                        "self_rating": "3",
                        "manager_rating": "4",
                    },
                    {
                        "emp_id": "EMP-0001",
                        "item_type": "COMPETENCY",
                        "item_id": "C1",
                        "self_rating": "3",
                        "manager_rating": "4",
                    },
                ]
                ratings[0][field] = value
                loaded = self._load(ratings=ratings)
                self.assertEqual(
                    loaded[3]["EMP-0001"], "INVALID_RATING"
                )

    def test_br07_each_goal_and_at_least_one_competency_need_ratings(self):
        goal_rating = {
            "emp_id": "EMP-0001",
            "item_type": "GOAL",
            "item_id": "G1",
            "self_rating": "3",
            "manager_rating": "4",
        }
        competency_rating = {
            "emp_id": "EMP-0001",
            "item_type": "COMPETENCY",
            "item_id": "C1",
            "self_rating": "3",
            "manager_rating": "4",
        }
        for ratings in ([competency_rating], [goal_rating]):
            with self.subTest(ratings=ratings):
                loaded = self._load(ratings=deepcopy(ratings))
                self.assertEqual(
                    loaded[3]["EMP-0001"], "INVALID_RATING"
                )

    def test_br07_employee_specific_competency_requirements_override_default(self):
        catalog = {
            "status": "OFFICIAL",
            "provenance": "Test-specific requirement",
            "competency_ids": ["C1", "C2"],
            "default_required_competencies": ["C1"],
            "employee_required_competencies": {
                "EMP-0001": ["C2"],
            },
        }
        ratings = [
            {
                "emp_id": "EMP-0001",
                "item_type": "GOAL",
                "item_id": "G1",
                "self_rating": "3",
                "manager_rating": "4",
            },
            {
                "emp_id": "EMP-0001",
                "item_type": "COMPETENCY",
                "item_id": "C2",
                "self_rating": "3",
                "manager_rating": "4",
            },
        ]
        loaded = self._load(ratings=ratings, catalog=catalog)
        self.assertNotIn("EMP-0001", loaded[3])
        ratings = [
            row for row in ratings
            if row["item_type"] != "COMPETENCY"
        ]
        ratings.append({
            "emp_id": "EMP-0001",
            "item_type": "COMPETENCY",
            "item_id": "C1",
            "self_rating": "3",
            "manager_rating": "4",
        })
        loaded = self._load(ratings=ratings, catalog=catalog)
        self.assertEqual(loaded[3]["EMP-0001"], "INVALID_RATING")

    def test_br07_missing_required_competency_marks_employee_invalid(self):
        catalog = {
            "status": "PROVISIONAL",
            "provenance": "Test fixture",
            "competency_ids": ["C1", "C2"],
            "default_required_competencies": ["C1", "C2"],
            "employee_required_competencies": {},
        }
        loaded = self._load(catalog=catalog)
        self.assertEqual(loaded[3]["EMP-0001"], "INVALID_RATING")

    def test_br07_duplicate_competency_rating_marks_employee_invalid(self):
        ratings = [
            {
                "emp_id": "EMP-0001",
                "item_type": "GOAL",
                "item_id": "G1",
                "self_rating": "3",
                "manager_rating": "4",
            },
            {
                "emp_id": "EMP-0001",
                "item_type": "COMPETENCY",
                "item_id": "C1",
                "self_rating": "3",
                "manager_rating": "4",
            },
            {
                "emp_id": "EMP-0001",
                "item_type": "COMPETENCY",
                "item_id": "C1",
                "self_rating": "3",
                "manager_rating": "4",
            },
        ]
        loaded = self._load(ratings=ratings)
        self.assertEqual(loaded[3]["EMP-0001"], "INVALID_RATING")

    def test_br07_unknown_competency_rating_marks_employee_invalid(self):
        ratings = [
            {
                "emp_id": "EMP-0001",
                "item_type": "GOAL",
                "item_id": "G1",
                "self_rating": "3",
                "manager_rating": "4",
            },
            {
                "emp_id": "EMP-0001",
                "item_type": "COMPETENCY",
                "item_id": "UNKNOWN",
                "self_rating": "3",
                "manager_rating": "4",
            },
        ]
        loaded = self._load(ratings=ratings)
        self.assertEqual(loaded[3]["EMP-0001"], "INVALID_RATING")

    def test_competency_catalog_rejects_duplicate_or_undefined_requirements(self):
        catalogs = (
            {
                "status": "PROVISIONAL",
                "provenance": "Test fixture",
                "competency_ids": ["C1", "C1"],
                "default_required_competencies": ["C1"],
                "employee_required_competencies": {},
            },
            {
                "status": "PROVISIONAL",
                "provenance": "Test fixture",
                "competency_ids": ["C1"],
                "default_required_competencies": ["C2"],
                "employee_required_competencies": {},
            },
            {
                "status": "PROVISIONAL",
                "provenance": "Test fixture",
                "competency_ids": ["C1"],
                "default_required_competencies": ["C1"],
                "employee_required_competencies": {
                    "EMP-0001": ["C1", "C1"],
                },
            },
        )
        for catalog in catalogs:
            with self.subTest(catalog=catalog):
                with self.assertRaisesRegex(ValueError, "competency"):
                    self._load(catalog=catalog)

    def test_competency_catalog_must_be_explicit_and_have_provenance(self):
        catalog = {
            "status": "PROVISIONAL",
            "competency_ids": ["C1"],
            "default_required_competencies": ["C1"],
            "employee_required_competencies": {},
        }
        with self.assertRaisesRegex(ValueError, "provenance"):
            self._load(catalog=catalog)


if __name__ == "__main__":
    unittest.main()
