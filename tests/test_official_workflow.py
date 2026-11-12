import csv
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.appeals import process_appeal
from src.calibration import distribute_ratings
from src.compensation import calculate_scaled_increment_rates
from src.compensation import calculate_proration
from src.models import Employee, Goal, Rating
from src.official_data import load_official_data
from src.reports import (
    APPEAL_CHANGES_COLUMNS,
    DISTRIBUTION_COLUMNS,
    LETTERS_COLUMNS,
    write_appeal_changes,
    write_distribution,
    write_letters,
)
from src.scoring import calculate_raw_scores
from src.workflow import run_commands


class TestOfficialData(unittest.TestCase):
    def write_csv(self, folder, name, columns, rows):
        path = folder / name
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_official_schema_skips_duplicate_rating_and_marks_bad_weights(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            employees = self.write_csv(
                folder,
                "employees.csv",
                [
                    "emp_id", "name", "unit", "grade", "basic_salary",
                    "date_of_joining", "manager_id", "months_in_grade",
                    "previous_year_rating", "role_band",
                ],
                [
                    {
                        "emp_id": "EMP-0001", "name": "One", "unit": "ENGINEERING",
                        "grade": "G3", "basic_salary": "30000.00",
                        "date_of_joining": "2020-01-01", "manager_id": "M1",
                        "months_in_grade": "36", "previous_year_rating": "3",
                        "role_band": "IC",
                    },
                    {
                        "emp_id": "EMP-0002", "name": "Two", "unit": "ENGINEERING",
                        "grade": "G3", "basic_salary": "30000.00",
                        "date_of_joining": "2020-01-01", "manager_id": "M1",
                        "months_in_grade": "36", "previous_year_rating": "3",
                        "role_band": "IC",
                    },
                ],
            )
            goals = self.write_csv(
                folder,
                "goals.csv",
                ["emp_id", "goal_id", "goal_title", "weight"],
                [
                    {"emp_id": "EMP-0001", "goal_id": "G1", "goal_title": "A", "weight": 100},
                    {"emp_id": "EMP-0002", "goal_id": "G2", "goal_title": "B", "weight": 99},
                ],
            )
            ratings = self.write_csv(
                folder,
                "ratings.csv",
                ["emp_id", "item_type", "item_id", "self_rating", "manager_rating"],
                [
                    {"emp_id": "EMP-0001", "item_type": "GOAL", "item_id": "G1", "self_rating": 3, "manager_rating": 4},
                    {"emp_id": "EMP-0001", "item_type": "GOAL", "item_id": "G1", "self_rating": 3, "manager_rating": 4},
                    {"emp_id": "EMP-0001", "item_type": "COMPETENCY", "item_id": "C1", "self_rating": 3, "manager_rating": 4},
                    {"emp_id": "EMP-0002", "item_type": "GOAL", "item_id": "G2", "self_rating": 3, "manager_rating": 4},
                    {"emp_id": "EMP-0002", "item_type": "COMPETENCY", "item_id": "C1", "self_rating": 3, "manager_rating": 4},
                ],
            )
            bands = self.write_csv(
                folder,
                "grade_bands.csv",
                ["grade", "band_min", "band_max"],
                [
                    {"grade": f"G{grade}", "band_min": "18000.00", "band_max": "30000.00"}
                    for grade in range(1, 8)
                ],
            )
            units = self.write_csv(
                folder,
                "units.csv",
                ["unit", "increment_budget_annual", "unit_head"],
                [{"unit": "ENGINEERING", "increment_budget_annual": "500000", "unit_head": "M1"}],
            )
            competency_catalog = folder / "competency_catalog.json"
            competency_catalog.write_text(
                json.dumps({
                    "status": "PROVISIONAL",
                    "provenance": "Test fixture",
                    "competency_ids": ["C1"],
                    "default_required_competencies": ["C1"],
                    "employee_required_competencies": {},
                }),
                encoding="utf-8",
            )

            loaded = load_official_data(
                employees,
                goals,
                ratings,
                bands,
                units,
                date(2026, 9, 30),
                competency_catalog_path=competency_catalog,
            )

        loaded_employees, _, loaded_ratings, statuses, loaded_bands, budgets = loaded
        self.assertEqual(statuses, {"EMP-0002": "INVALID_WEIGHTS"})
        self.assertEqual(
            sum(r.employee_id == "EMP-0001" for r in loaded_ratings), 2
        )
        self.assertEqual(loaded_bands["G3"], {
            "band_min": 18000.0,
            "band_max": 30000.0,
        })
        self.assertEqual(budgets, {"ENGINEERING": 500000.0})
        self.assertEqual(loaded_employees["EMP-0001"].months_in_grade, 36)

    def test_commands_cannot_run_appraisal_before_load(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            command_file = Path(temp_dir) / "commands.txt"
            command_file.write_text(
                "SET_APPRAISAL_YEAR|2026|2026-09-30\n"
                "SET_COMPANY_MULTIPLIER|1.05\n"
                "RUN_APPRAISAL\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "LOAD must precede"):
                run_commands(command_file, Path(temp_dir) / "output")


class TestOfficialAppeals(unittest.TestCase):
    def setUp(self):
        self.employee = Employee(
            "EMP-0001", "IT", "G3", 30000, date(2020, 1, 1), "M1",
            "IC", date(2020, 1, 1),
        )
        self.employees = {self.employee.employee_id: self.employee}
        self.goals = [Goal("EMP-0001", "G1", "Goal", 100)]
        self.ratings = [
            Rating("EMP-0001", "GOAL", "G1", 3, 3),
            Rating("EMP-0001", "COMPETENCY", "C1", 3, 3),
        ]
        for number in range(2, 11):
            employee_id = f"EMP-{number:04d}"
            employee = Employee(
                employee_id, "IT", "G3", 30000, date(2020, 1, 1), "M1",
                "IC", date(2020, 1, 1),
            )
            self.employees[employee_id] = employee
            self.goals.append(
                Goal(employee_id, f"G{number}", "Goal", 100)
            )
            self.ratings.extend([
                Rating(employee_id, "GOAL", f"G{number}", 3, 3),
                Rating(employee_id, "COMPETENCY", "C1", 3, 3),
            ])
        self.eligibility = {"EMP-0001": "ELIGIBLE"}
        self.eligibility.update({
            employee_id: "ELIGIBLE"
            for employee_id in self.employees
            if employee_id != "EMP-0001"
        })
        self.scores = calculate_raw_scores(
            self.employees, self.goals, self.ratings
        )
        self.results = distribute_ratings(
            self.employees, self.scores, self.eligibility, 2026
        )

    def test_official_target_rating_is_applied(self):
        scores, results, _ = process_appeal(
            self.employees,
            self.goals,
            self.ratings,
            self.scores,
            self.results,
            self.eligibility,
            "EMP-0001",
            ["G1"],
            2026,
            new_ratings={"G1": 4},
        )
        self.assertEqual(self.ratings[0].manager_rating, 4)
        self.assertEqual(scores["EMP-0001"]["goal_score"], 4.0)
        self.assertIn(results["EMP-0001"]["final_rating"], range(1, 6))

    def test_more_than_one_point_is_rejected_without_mutation(self):
        with self.assertRaisesRegex(ValueError, "at most one point"):
            process_appeal(
                self.employees,
                self.goals,
                self.ratings,
                self.scores,
                self.results,
                self.eligibility,
                "EMP-0001",
                ["G1"],
                2026,
                new_ratings={"G1": 5},
            )
        self.assertEqual(self.ratings[0].manager_rating, 3)


class TestOfficialBudgetsAndReports(unittest.TestCase):
    def test_cutoff_day_joiner_gets_documented_april_to_september_proration(self):
        self.assertEqual(
            calculate_proration(
                date(2026, 9, 30),
                2026,
                date(2026, 9, 30),
                through_cutoff=True,
            ),
            0.5,
        )

    def test_annual_budget_scaling_accounts_for_salary_floor(self):
        employee = Employee(
            "EMP-0126", "OPERATIONS", "G1", 23800, date(2025, 1, 1),
            "M1", "IC", date(2024, 1, 1), previous_final_rating=3,
        )
        rates = calculate_scaled_increment_rates(
            {"EMP-0126": employee},
            {"EMP-0126": {"final_rating": 3}},
            2026,
            {"OPERATIONS": 20000},
            appraisal_cutoff_date=date(2026, 9, 30),
            proration_through_cutoff=True,
            annualize_cost=True,
            grade_bands={
                f"G{grade}": {"band_min": 18000, "band_max": 30000}
                for grade in range(1, 8)
            },
        )
        revised = max(
            25000,
            ((employee.basic_salary * (1 + rates["EMP-0126"]) + 99) // 100) * 100,
        )
        self.assertGreaterEqual(revised, 25000)
        self.assertLessEqual((revised - employee.basic_salary) * 12, 20000)

    def test_report_headers_match_official_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            paths = {
                "letters.csv": (LETTERS_COLUMNS, write_letters),
                "distribution.csv": (DISTRIBUTION_COLUMNS, write_distribution),
                "appeal_changes.csv": (APPEAL_CHANGES_COLUMNS, write_appeal_changes),
            }
            for name, (columns, writer) in paths.items():
                with self.subTest(name=name):
                    target = folder / name
                    writer(target, [])
                    with target.open(newline="", encoding="utf-8") as file:
                        self.assertEqual(next(csv.reader(file)), columns)


if __name__ == "__main__":
    unittest.main()
