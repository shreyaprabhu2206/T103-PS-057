
import unittest
from datetime import date

from src.models import Employee
from src.calibration import check_eligibility


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


if __name__ == "__main__":
    unittest.main()
