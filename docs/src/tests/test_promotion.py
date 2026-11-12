
import unittest
from datetime import date
from types import SimpleNamespace

from src.models import Employee
from src.promotion import (
    check_promotion_eligibility,
    select_promotions,
)


class TestPromotionEligibility(unittest.TestCase):

    appraisal_date = date(2026, 9, 30)

    def create_employee(self, grade_start_date):
        return SimpleNamespace(
            grade_start_date=grade_start_date
        )

    def test_rating_5_eligible(self):
        employee = self.create_employee(date(2024, 1, 1))

        result = check_promotion_eligibility(
            employee, 5, self.appraisal_date
        )

        self.assertTrue(result)

    def test_rating_5_not_eligible(self):
        employee = self.create_employee(date(2025, 5, 1))

        result = check_promotion_eligibility(
            employee, 5, self.appraisal_date
        )

        self.assertFalse(result)

    def test_rating_4_eligible(self):
        employee = self.create_employee(date(2023, 1, 1))

        result = check_promotion_eligibility(
            employee, 4, self.appraisal_date
        )

        self.assertTrue(result)

    def test_rating_3_not_eligible(self):
        employee = self.create_employee(date(2020, 1, 1))

        result = check_promotion_eligibility(
            employee, 3, self.appraisal_date
        )

        self.assertFalse(result)

    def create_workflow_employee(
        self, employee_id, business_unit, grade_start_date
    ):
        return Employee(
            employee_id=employee_id,
            business_unit=business_unit,
            grade="G3",
            basic_salary=30000,
            joining_date=date(2020, 1, 1),
            manager_id="M001",
            current_role_band="B3",
            grade_start_date=grade_start_date,
        )

    def test_rating_5_eligibility_at_exact_24_months(self):
        employee = self.create_employee(date(2024, 9, 30))

        self.assertTrue(
            check_promotion_eligibility(
                employee, 5, date(2026, 9, 30)
            )
        )

    def test_rating_4_eligibility_at_exact_36_months(self):
        employee = self.create_employee(date(2023, 9, 30))

        self.assertTrue(
            check_promotion_eligibility(
                employee, 4, date(2026, 9, 30)
            )
        )

    def test_promotion_months_use_configured_evaluation_date(self):
        employee = self.create_employee(date(2024, 10, 1))

        self.assertFalse(
            check_promotion_eligibility(
                employee, 5, date(2026, 9, 30)
            )
        )
        self.assertTrue(
            check_promotion_eligibility(
                employee, 5, date(2026, 10, 1)
            )
        )

    def test_promotion_limit_uses_ceiling_and_selects_highest_raw_scores(self):
        appraisal_date = date(2026, 9, 30)
        employees = {}
        final_results = {}
        eligibility = {}
        scores = {}

        for index in range(13):
            employee_id = f"E{index:03d}"
            employees[employee_id] = self.create_workflow_employee(
                employee_id,
                "IT",
                date(2023, 1, 1),
            )
            final_results[employee_id] = {
                "final_rating": 5 if index < 3 else 3,
            }
            eligibility[employee_id] = "ELIGIBLE"
            scores[employee_id] = {
                "raw_score": {0: 4.2, 1: 4.8, 2: 4.5}.get(index, 3.0),
            }

        selected = select_promotions(
            employees,
            final_results,
            scores,
            eligibility,
            appraisal_date,
        )

        self.assertEqual(selected, {"E001", "E002"})

    def test_promotion_selection_does_not_change_grade_or_tenure(self):
        appraisal_date = date(2026, 9, 30)
        employee = self.create_workflow_employee(
            "E001", "IT", date(2023, 1, 1)
        )
        original_grade_start_date = employee.grade_start_date
        employees = {"E001": employee}
        final_results = {"E001": {"final_rating": 5}}
        scores = {"E001": {"raw_score": 4.5}}
        eligibility = {"E001": "ELIGIBLE"}

        selected = select_promotions(
            employees,
            final_results,
            scores,
            eligibility,
            appraisal_date,
        )

        self.assertEqual(selected, {"E001"})
        self.assertEqual(employee.grade, "G3")
        self.assertEqual(employee.grade_start_date, original_grade_start_date)


if __name__ == "__main__":
    unittest.main()
