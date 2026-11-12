
import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.models import Employee
from src.compensation import (
    calculate_compensation,
    calculate_proration,
    calculate_scaled_increment_rates,
    calculate_variable_pay,
    load_company_multiplier,
)


class TestCompensation(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.grade_bands_path = Path(self.temp_dir.name) / "grade_bands.csv"
        test_band_maxima = {
            "G1": 15000,
            "G2": 22000,
            "G3": 33000,
            "G4": 33500,
            "G5": 50000,
            "G6": 70000,
            "G7": 100000,
        }

        with self.grade_bands_path.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=["grade", "band_min", "band_max"]
            )
            writer.writeheader()
            for grade, band_max in test_band_maxima.items():
                writer.writerow({
                    "grade": grade,
                    "band_min": 1,
                    "band_max": band_max,
                })

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_employee(
        self, salary=30000, joining_date=None, previous_final_rating=3
    ):
        return Employee(
            employee_id="E001",
            business_unit="IT",
            grade="G3",
            basic_salary=salary,
            joining_date=joining_date or date(2023, 6, 15),
            manager_id="M001",
            current_role_band="B3",
            grade_start_date=date(2023, 1, 1),
            previous_final_rating=previous_final_rating
        )

    def test_rating_5_increment(self):
        employee = self.create_employee()

        result = calculate_compensation(employee, 5, 2025)

        self.assertEqual(result["increment_rate"], 0.14)
        self.assertEqual(result["revised_salary"], 34200)

    def test_rating_3_increment(self):
        employee = self.create_employee()

        result = calculate_compensation(employee, 3, 2025)

        self.assertEqual(result["increment_rate"], 0.06)
        self.assertEqual(result["revised_salary"], 31800)

    def test_full_proration_for_existing_employee(self):
        employee = self.create_employee(
            joining_date=date(2024, 1, 1)
        )

        result = calculate_proration(
            employee.joining_date, 2025
        )

        self.assertEqual(result, 1.0)

    def test_zero_proration_after_cutoff(self):
        employee = self.create_employee(
            joining_date=date(2025, 10, 1)
        )

        result = calculate_proration(
            employee.joining_date, 2025
        )

        self.assertEqual(result, 0.0)

    def test_proration_uses_configured_year_and_cutoff(self):
        joining_date = date(2026, 10, 1)

        self.assertAlmostEqual(
            calculate_proration(
                joining_date,
                2026,
                date(2026, 10, 31),
            ),
            5 / 12,
        )
        self.assertEqual(
            calculate_proration(
                joining_date,
                2026,
                date(2026, 9, 30),
            ),
            0.0,
        )

    def test_salary_rounding(self):
        employee = self.create_employee(
            salary=30001,
            joining_date=date(2024, 1, 1)
        )

        result = calculate_compensation(employee, 2, 2025)

        self.assertEqual(result["revised_salary"], 30700)

    def test_minimum_salary_floor_for_rating_3_or_above(self):
        employee = self.create_employee(
            salary=20000,
            joining_date=date(2024, 1, 1)
        )

        result = calculate_compensation(employee, 3, 2025)

        self.assertEqual(result["revised_salary"], 25000)

    def test_minimum_salary_floor_not_applied_below_rating_3(self):
        employee = self.create_employee(
            salary=20000,
            joining_date=date(2024, 1, 1)
        )

        result = calculate_compensation(employee, 2, 2025)

        self.assertEqual(result["revised_salary"], 20400)

    def test_budget_scaling_preserves_minimum_salary_floor(self):
        employee = self.create_employee(
            salary=20000,
            joining_date=date(2024, 1, 1),
        )
        employees = {employee.employee_id: employee}
        final_results = {
            employee.employee_id: {"final_rating": 3}
        }

        scaled_rates = calculate_scaled_increment_rates(
            employees,
            final_results,
            2025,
            {"IT": 200},
        )
        result = calculate_compensation(
            employee,
            3,
            2025,
            increment_rate_override=scaled_rates[employee.employee_id],
        )

        self.assertEqual(scaled_rates["E001"], 0.009)
        self.assertEqual(result["increment_rate"], 0.009)
        self.assertEqual(result["revised_salary"], 25000)

    def test_budget_scaling_does_not_apply_promotion_increment_twice(self):
        employee = self.create_employee(
            salary=30000,
            joining_date=date(2024, 1, 1),
        )
        employees = {employee.employee_id: employee}
        final_results = {
            employee.employee_id: {"final_rating": 5}
        }
        scaled_rates = calculate_scaled_increment_rates(
            employees,
            final_results,
            2025,
            {"IT": 2850},
            promoted_employee_ids={"E001"},
        )

        result = calculate_compensation(
            employee,
            5,
            2025,
            is_promotion=True,
            increment_rate_override=scaled_rates["E001"],
        )

        self.assertEqual(scaled_rates["E001"], 0.095)
        self.assertEqual(result["increment_rate"], 0.095)
        self.assertAlmostEqual(result["promotion_increment_rate"], 0.025)
        self.assertEqual(result["revised_salary"], 32900)

    def test_grade_band_normal_case_below_cap(self):
        employee = self.create_employee(salary=30000)

        result = calculate_compensation(
            employee, 3, 2025, grade_bands_path=self.grade_bands_path
        )

        self.assertEqual(result["revised_salary"], 31800)
        self.assertEqual(result["lump_sum"], 0)
        self.assertEqual(result["grade_band_max"], 33000)

    def test_grade_cap_pays_excess_as_lump_sum(self):
        employee = self.create_employee(salary=30000)

        result = calculate_compensation(
            employee, 5, 2025, grade_bands_path=self.grade_bands_path
        )

        self.assertEqual(result["revised_salary"], 33000)
        self.assertEqual(result["lump_sum"], 1200)

    def test_salary_exactly_at_grade_max_has_no_lump_sum(self):
        employee = self.create_employee(salary=30000)

        result = calculate_compensation(
            employee, 4, 2025, grade_bands_path=self.grade_bands_path
        )

        self.assertEqual(result["revised_salary"], 33000)
        self.assertEqual(result["lump_sum"], 0)

    def test_promotion_uses_explicit_new_grade_band(self):
        employee = self.create_employee(salary=30000)

        result = calculate_compensation(
            employee,
            5,
            2025,
            grade_bands_path=self.grade_bands_path,
            new_grade="G4",
        )

        self.assertEqual(result["grade"], "G4")
        self.assertEqual(result["grade_band_max"], 33500)
        self.assertEqual(result["revised_salary"], 33500)
        self.assertEqual(result["lump_sum"], 700)

    def test_selected_promotion_adds_five_percent_increment(self):
        employee = self.create_employee(salary=30000)

        result = calculate_compensation(
            employee, 5, 2025, is_promotion=True
        )

        self.assertEqual(result["promotion_increment_rate"], 0.05)
        self.assertEqual(result["increment_rate"], 0.19)
        self.assertEqual(result["revised_salary"], 35700)

    def test_rating_1_places_employee_on_pip_and_zeros_increment(self):
        employee = self.create_employee(salary=30001)

        result = calculate_compensation(employee, 1, 2025)

        self.assertTrue(result["on_pip"])
        self.assertEqual(result["increment_rate"], 0)
        self.assertEqual(result["increment_amount"], 0)
        self.assertEqual(result["revised_salary"], 30001)

    def test_consecutive_rating_2_places_employee_on_pip(self):
        employee = self.create_employee(previous_final_rating=2)

        result = calculate_compensation(employee, 2, 2025)

        self.assertTrue(result["on_pip"])
        self.assertEqual(result["increment_rate"], 0)
        self.assertEqual(result["revised_salary"], 30000)

    def test_nonconsecutive_rating_2_does_not_place_employee_on_pip(self):
        employee = self.create_employee(previous_final_rating=3)

        result = calculate_compensation(employee, 2, 2025)

        self.assertFalse(result["on_pip"])
        self.assertEqual(result["increment_rate"], 0.02)
        self.assertEqual(result["revised_salary"], 30600)

    def test_invalid_rating(self):
        employee = self.create_employee()

        with self.assertRaises(ValueError):
            calculate_compensation(employee, 6, 2025)

    def test_variable_pay_all_rating_multipliers(self):
        employee = self.create_employee(salary=10000)
        expected = {
            5: 28350,
            4: 22680,
            3: 18900,
            2: 9450,
            1: 0,
        }

        for rating, payout in expected.items():
            with self.subTest(rating=rating):
                self.assertEqual(
                    calculate_variable_pay(employee, rating, 1.05),
                    payout,
                )

    def test_variable_pay_grade_target_groups(self):
        expected = {
            "G1": 18000,
            "G2": 18000,
            "G3": 18000,
            "G4": 24000,
            "G5": 24000,
            "G6": 36000,
            "G7": 36000,
        }

        for grade, payout in expected.items():
            employee = self.create_employee(salary=10000)
            employee.grade = grade
            with self.subTest(grade=grade):
                self.assertEqual(
                    calculate_variable_pay(employee, 3, 1.0),
                    payout,
                )

    def test_variable_pay_uses_configured_company_multiplier(self):
        employee = self.create_employee(salary=10000)

        self.assertEqual(
            calculate_variable_pay(employee, 3, 1.05),
            18900,
        )

    def test_variable_pay_rounds_half_rupee_up(self):
        employee = self.create_employee(salary=100)
        employee.grade = "G1"

        self.assertEqual(
            calculate_variable_pay(employee, 5, 1.05),
            284,
        )

    def test_pip_employee_receives_zero_variable_pay(self):
        employee = self.create_employee(salary=30000)

        result = calculate_compensation(
            employee, 1, 2025, company_multiplier=1.05
        )

        self.assertTrue(result["on_pip"])
        self.assertEqual(result["variable_pay"], 0)

    def test_consecutive_rating_2_pip_employee_receives_zero_variable_pay(self):
        employee = self.create_employee(
            salary=30000, previous_final_rating=2
        )

        result = calculate_compensation(
            employee, 2, 2025, company_multiplier=1.05
        )

        self.assertTrue(result["on_pip"])
        self.assertEqual(result["variable_pay"], 0)

    def test_load_company_multiplier_from_command(self):
        commands_path = Path(self.temp_dir.name) / "commands.txt"
        commands_path.write_text(
            "SET_COMPANY_MULTIPLIER|1.05\n",
            encoding="utf-8",
        )

        self.assertEqual(load_company_multiplier(commands_path), 1.05)


if __name__ == "__main__":
    unittest.main()
