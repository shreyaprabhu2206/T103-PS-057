import contextlib
import csv
import io
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from src.workflow import run_commands


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestOfficialSampleEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.output_dir = Path(cls.temp_dir.name)
        with contextlib.redirect_stdout(io.StringIO()):
            cls.workflow = run_commands(
                PROJECT_ROOT / "commands.txt",
                cls.output_dir,
            )
        cls.letters, cls.letter_headers = cls._read_report("letters.csv")
        cls.distribution, cls.distribution_headers = cls._read_report(
            "distribution.csv"
        )
        cls.appeal_changes, cls.appeal_headers = cls._read_report(
            "appeal_changes.csv"
        )
        with (PROJECT_ROOT / "data" / "input" / "employees.csv").open(
            "r", newline="", encoding="utf-8-sig"
        ) as file:
            cls.source_employees = {
                row["emp_id"]: row for row in csv.DictReader(file)
            }
        cls.letters_by_id = {
            row["emp_id"]: row for row in cls.letters
        }

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    @classmethod
    def _read_report(cls, filename):
        path = cls.output_dir / filename
        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader), reader.fieldnames

    def test_ec1_exactly_ten_stays_separate_and_nine_pools_forward(self):
        first_print = [
            row for row in self.distribution if row["print_no"] == "1"
        ]
        unit_rows = {}
        for row in first_print:
            unit_rows[row["unit_or_pool"]] = row["eligible_count"]

        self.assertEqual(unit_rows["FINANCE"], "10")
        self.assertIn("HR+LEGAL", unit_rows)
        self.assertNotIn("HR", unit_rows)
        self.assertNotIn("LEGAL", unit_rows)

    def test_ec2_identical_scores_and_tenure_use_lower_employee_id(self):
        first = self.workflow.final_results["EMP-0111"]
        second = self.workflow.final_results["EMP-0112"]
        first_score = self.workflow.scores["EMP-0111"]
        second_score = self.workflow.scores["EMP-0112"]

        self.assertEqual(first_score["raw_score"], second_score["raw_score"])
        self.assertEqual(first_score["goal_score"], second_score["goal_score"])
        self.assertLess(first["rank"], second["rank"])

    def test_ec3_cutoff_date_joiner_is_prorated_and_next_day_is_excluded(self):
        cutoff_joiner = self.workflow.compensation["EMP-0080"]
        self.assertEqual(cutoff_joiner["proration"], 0.5)
        self.assertEqual(self.letters_by_id["EMP-0080"]["status_code"], "OK")
        self.assertEqual(
            self.letters_by_id["EMP-0081"]["status_code"], "NOT_ELIGIBLE"
        )
        self.assertNotIn("EMP-0081", self.workflow.compensation)
        self.assertEqual(self.letters_by_id["EMP-0081"]["increment_pct"], "")
        self.assertEqual(self.letters_by_id["EMP-0081"]["revised_basic"], "")
        distributed_ids = {
            employee_id
            for row in self.distribution
            for employee_id in row["emp_ids"].split(",")
            if employee_id
        }
        self.assertNotIn("EMP-0081", distributed_ids)

    def test_ec4_revised_basic_at_grade_max_has_no_lump_sum(self):
        compensation = self.workflow.compensation["EMP-0011"]
        self.assertEqual(compensation["final_rating"], 3)
        self.assertEqual(compensation["grade_band_max"], 60000)
        self.assertEqual(compensation["revised_salary"], 60000)
        self.assertEqual(compensation["lump_sum"], 0)

    def test_ec5_sales_promotions_obey_ceil_eight_percent_cap(self):
        sales_ids = [
            employee_id
            for employee_id, employee in self.workflow.data[0].items()
            if employee.business_unit == "SALES"
            and self.workflow.eligibility[employee_id] == "ELIGIBLE"
        ]
        self.assertEqual(len(sales_ids), 35)
        grade_order = list(self.workflow.data[4])
        promotion_candidates = []
        for employee_id in sales_ids:
            source = self.source_employees[employee_id]
            rating = self.workflow.final_results[employee_id]["final_rating"]
            months_in_grade = int(source["months_in_grade"])
            rating_eligible = (
                rating == 5 and months_in_grade >= 24
            ) or (
                rating == 4 and months_in_grade >= 36
            )
            if (
                rating_eligible
                and source["grade"] != grade_order[-1]
            ):
                promotion_candidates.append(employee_id)
        expected_top_three = set(sorted(
            promotion_candidates,
            key=lambda employee_id: (
                -self.workflow.scores[employee_id]["raw_score"],
            ),
        )[:3])
        selected = self.workflow.promoted_employee_ids & set(sales_ids)
        self.assertEqual(len(selected), 3)
        self.assertEqual(selected, expected_top_three)

    def test_promotions_advance_grade_reset_tenure_and_respect_new_band_cap(self):
        grade_order = list(self.workflow.data[4])
        self.assertEqual(
            grade_order, ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]
        )
        for employee_id, new_grade in self.workflow.promoted_grades.items():
            with self.subTest(employee_id=employee_id):
                old_grade = self.source_employees[employee_id]["grade"]
                expected_grade = grade_order[
                    grade_order.index(old_grade) + 1
                ]
                employee = self.workflow.data[0][employee_id]
                compensation = self.workflow.compensation[employee_id]
                self.assertEqual(new_grade, expected_grade)
                self.assertEqual(employee.grade, expected_grade)
                self.assertEqual(employee.months_in_grade, 0)
                self.assertEqual(compensation["grade"], expected_grade)
                self.assertLessEqual(
                    compensation["revised_salary"],
                    self.workflow.data[4][expected_grade]["band_max"],
                )
                self.assertEqual(
                    self.letters_by_id[employee_id]["new_grade"],
                    expected_grade,
                )
                self.assertLessEqual(
                    compensation["increment_rate"],
                    {
                        5: 0.19,
                        4: 0.15,
                        3: 0.11,
                        2: 0.07,
                        1: 0.00,
                    }[compensation["final_rating"]],
                )

    def test_ec6_appeal_changes_top_ten_percent_boundary(self):
        def ids_for(print_no, rating):
            return {
                employee_id
                for row in self.distribution
                if row["print_no"] == str(print_no)
                and row["unit_or_pool"] == "ENGINEERING"
                and row["rating"] == str(rating)
                for employee_id in row["emp_ids"].split(",")
                if employee_id
            }

        self.assertIn("EMP-0007", ids_for(1, 5))
        self.assertNotIn("EMP-0008", ids_for(1, 5))
        self.assertIn("EMP-0008", ids_for(2, 5))
        self.assertNotIn("EMP-0007", ids_for(2, 5))
        self.assertEqual(
            self.appeal_changes,
            [
                {
                    "appeal_id": "APL-01",
                    "unit_or_pool": "ENGINEERING",
                    "emp_id": "EMP-0007",
                    "rating_before": "5",
                    "rating_after": "4",
                },
                {
                    "appeal_id": "APL-01",
                    "unit_or_pool": "ENGINEERING",
                    "emp_id": "EMP-0008",
                    "rating_before": "4",
                    "rating_after": "5",
                },
            ],
        )

    def test_ec7_budget_scaling_preserves_the_minimum_salary_floor(self):
        self.assertEqual(
            self.workflow.compensation["EMP-0126"]["revised_salary"],
            25000,
        )
        employees = self.workflow.data[0]
        budgets = self.workflow.data[5]
        costs = Counter()
        for employee_id, compensation in self.workflow.compensation.items():
            employee = employees[employee_id]
            costs[employee.business_unit] += max(
                0,
                compensation["revised_salary"] - employee.basic_salary,
            ) * 12
        for unit, annual_cost in costs.items():
            with self.subTest(unit=unit):
                self.assertLessEqual(annual_cost, budgets[unit] + 0.01)

    def test_ec8_goal_weights_99_and_101_are_invalid(self):
        statuses = self.workflow.data[3]
        self.assertEqual(statuses["EMP-0094"], "INVALID_WEIGHTS")
        self.assertEqual(statuses["EMP-0095"], "INVALID_WEIGHTS")
        self.assertIsNone(self.workflow.final_results["EMP-0094"]["final_rating"])
        self.assertIsNone(self.workflow.final_results["EMP-0095"]["final_rating"])

    def test_documented_extra_cases_and_report_shapes(self):
        self.assertEqual(self.workflow.company_multiplier, 1.05)
        self.assertEqual(
            self.workflow.compensation["EMP-0156"]["proration"], 0.25
        )
        self.assertTrue(self.workflow.compensation["EMP-0136"]["on_pip"])
        self.assertEqual(self.workflow.compensation["EMP-0136"]["variable_pay"], 0)
        self.assertTrue(self.workflow.compensation["EMP-0070"]["on_pip"])
        self.assertEqual(
            {
                employee_id
                for employee_id, status in self.workflow.data[3].items()
                if status == "INVALID_RATING"
            },
            {
                employee_id
                for employee_id, row in self.letters_by_id.items()
                if row["status_code"] == "INVALID_RATING"
            },
        )
        invalid_rating_ids = {
            employee_id
            for employee_id, status in self.workflow.data[3].items()
            if status == "INVALID_RATING"
        }
        self.assertEqual(len(invalid_rating_ids), 2)

        with (PROJECT_ROOT / "data" / "input" / "ratings.csv").open(
            "r", newline="", encoding="utf-8-sig"
        ) as file:
            input_rows = list(csv.DictReader(file))
        rating_keys = [
            (row["emp_id"], row["item_type"], row["item_id"])
            for row in input_rows
        ]
        duplicates = [
            key for key, count in Counter(rating_keys).items() if count > 1
        ]
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(
            sum(
                (rating.employee_id, rating.item_type, rating.item_id)
                == duplicates[0]
                for rating in self.workflow.data[2]
            ),
            1,
        )
        self.assertEqual(
            self.workflow.appeal_ids, {"APL-01", "APL-02", "APL-05"}
        )

        capped = [
            result for result in self.workflow.compensation.values()
            if result["lump_sum"] > 0
        ]
        self.assertTrue(all(
            result["revised_salary"] == result["grade_band_max"]
            for result in capped
        ))
        self.assertTrue(all(
            result["revised_salary"] <= result["grade_band_max"]
            for result in self.workflow.compensation.values()
        ))
        self.assertTrue(all(
            row["new_grade"] == (
                self.workflow.promoted_grades.get(row["emp_id"], "")
            )
            for row in self.letters
        ))
        self.assertEqual(len(self.letters), len(self.workflow.data[0]))
        self.assertEqual(
            [row["emp_id"] for row in self.letters],
            sorted(row["emp_id"] for row in self.letters),
        )
        self.assertEqual(
            self.letter_headers,
            [
                "emp_id", "unit", "eligible", "raw_score", "goal_score",
                "final_rating", "increment_pct", "pro_rated", "revised_basic",
                "lump_sum", "variable_payout", "promoted", "new_grade", "pip",
                "status_code",
            ],
        )
        self.assertEqual(
            self.distribution_headers,
            [
                "print_no", "unit_or_pool", "eligible_count", "rating",
                "bucket_size", "emp_ids",
            ],
        )
        self.assertEqual(
            self.appeal_headers,
            [
                "appeal_id", "unit_or_pool", "emp_id",
                "rating_before", "rating_after",
            ],
        )
        print_numbers = [int(row["print_no"]) for row in self.distribution]
        self.assertEqual(print_numbers, sorted(print_numbers))
        self.assertEqual(
            {row["print_no"] for row in self.distribution}, {"1", "2"}
        )

    def test_provisional_catalog_explicitly_matches_observed_sample_ids(self):
        catalog_path = PROJECT_ROOT / "data" / "input" / "competency_catalog.json"
        with catalog_path.open(encoding="utf-8") as file:
            catalog = json.load(file)
        with (PROJECT_ROOT / "data" / "input" / "ratings.csv").open(
            "r", newline="", encoding="utf-8-sig"
        ) as file:
            observed_ids = {
                row["item_id"].strip()
                for row in csv.DictReader(file)
                if row["item_type"].strip().upper() == "COMPETENCY"
            }

        self.assertEqual(catalog["status"], "PROVISIONAL")
        self.assertIn("not proof", catalog["provenance"])
        self.assertEqual(set(catalog["competency_ids"]), observed_ids)
        self.assertEqual(
            set(catalog["default_required_competencies"]), observed_ids
        )


if __name__ == "__main__":
    unittest.main()
