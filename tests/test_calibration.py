
import unittest
from datetime import date
import tempfile
from pathlib import Path

from src.models import Employee
from src.calibration import (
    check_eligibility,
    get_eligibility_results,
    load_appraisal_settings,
)


class TestEligibility(unittest.TestCase):

    def create_employee(self, joining_date):
        return Employee(
            employee_id="E001",
            business_unit="IT",
            grade="G3",
            basic_salary=30000,
            joining_date=joining_date,
            manager_id="M001",
            current_role_band="B3",
            grade_start_date=date(2023, 1, 1),
            previous_final_rating=3
        )

    def test_joined_before_cutoff(self):
        employee = self.create_employee(date(2025, 6, 15))
        self.assertEqual(
            check_eligibility(employee, 2025),
            "ELIGIBLE"
        )

    def test_joined_on_cutoff(self):
        employee = self.create_employee(date(2025, 9, 30))
        self.assertEqual(
            check_eligibility(employee, 2025),
            "ELIGIBLE"
        )

    def test_joined_after_cutoff(self):
        employee = self.create_employee(date(2025, 10, 1))
        self.assertEqual(
            check_eligibility(employee, 2025),
            "NOT_ELIGIBLE"
        )

    def test_custom_cutoff_controls_eligibility(self):
        employee = self.create_employee(date(2026, 10, 15))

        self.assertEqual(
            check_eligibility(
                employee, 2026, date(2026, 10, 31)
            ),
            "ELIGIBLE",
        )
        self.assertEqual(
            check_eligibility(
                employee, 2026, date(2026, 9, 30)
            ),
            "NOT_ELIGIBLE",
        )

    def test_eligibility_uses_configured_appraisal_year(self):
        employee = self.create_employee(date(2027, 10, 1))

        results = get_eligibility_results(
            {"E001": employee}, 2027, date(2027, 10, 31)
        )

        self.assertEqual(results["E001"], "ELIGIBLE")

    def test_load_appraisal_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            commands_path = Path(folder) / "commands.csv"
            commands_path.write_text(
                "SET_APPRAISAL_YEAR|2026|2026-10-31\n",
                encoding="utf-8",
            )

            self.assertEqual(
                load_appraisal_settings(commands_path),
                (2026, date(2026, 10, 31)),
            )

    def test_missing_appraisal_settings_has_clear_error(self):
        with tempfile.TemporaryDirectory() as folder:
            commands_path = Path(folder) / "commands.csv"
            commands_path.write_text(
                "SET_COMPANY_MULTIPLIER|1.05\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "missing SET_APPRAISAL_YEAR"
            ):
                load_appraisal_settings(commands_path)

    def test_invalid_appraisal_cutoff_has_clear_error(self):
        with tempfile.TemporaryDirectory() as folder:
            commands_path = Path(folder) / "commands.csv"
            commands_path.write_text(
                "SET_APPRAISAL_YEAR|2026|2026-02-30\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "cutoff date must use YYYY-MM-DD"
            ):
                load_appraisal_settings(commands_path)

    def test_invalid_appraisal_year_and_mismatched_cutoff_are_rejected(self):
        invalid_commands = (
            (
                "SET_APPRAISAL_YEAR|20x6|2026-09-30\n",
                "year must be a four-digit year",
            ),
            (
                "SET_APPRAISAL_YEAR|2026|2027-09-30\n",
                "cutoff date must be in the specified appraisal year",
            ),
        )
        with tempfile.TemporaryDirectory() as folder:
            commands_path = Path(folder) / "commands.csv"
            for content, message in invalid_commands:
                with self.subTest(content=content):
                    commands_path.write_text(content, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        load_appraisal_settings(commands_path)


if __name__ == "__main__":
    unittest.main()
