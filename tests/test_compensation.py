
import unittest
from datetime import date

from src.models import Employee
from src.compensation import (
    calculate_compensation,
    calculate_proration,
)


class TestCompensation(unittest.TestCase):

    def create_employee(self, salary=30000, joining_date=None):
        return Employee(
            employee_id="E001",
            business_unit="IT",
            grade="G3",
            basic_salary=salary,
            joining_date=joining_date or date(2023, 6, 15),
            manager_id="M001",
            current_role_band="B3",
            grade_start_date=date(2023, 1, 1),
            previous_final_rating=3
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

    def test_salary_rounding(self):
        employee = self.create_employee(
            salary=30001,
            joining_date=date(2024, 1, 1)
        )

        result = calculate_compensation(employee, 2, 2025)

        self.assertEqual(result["revised_salary"], 30700)

    def test_invalid_rating(self):
        employee = self.create_employee()

        with self.assertRaises(ValueError):
            calculate_compensation(employee, 6, 2025)


if __name__ == "__main__":
    unittest.main()
