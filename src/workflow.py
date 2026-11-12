from datetime import date
from pathlib import Path

from src.appeals import process_appeal
from src.calibration import (
    build_distribution_pools,
    distribute_ratings,
    get_eligibility_results,
)
from src.compensation import (
    calculate_compensation,
    calculate_scaled_increment_rates,
)
from src.official_data import INVALID_STATUSES, load_official_data
from src.promotion import next_grade_in_order, select_promotions
from src.reports import (
    distribution_rows,
    write_appeal_changes,
    write_distribution,
    write_letters,
)
from src.scoring import calculate_raw_scores


def _resolve_load_path(command_dir, value):
    path = Path(value)
    if path.is_absolute():
        return path
    candidates = (
        command_dir / path,
        command_dir / "data" / "input" / path,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"LOAD input file not found: {value!r} "
        f"(checked {candidates[0]} and {candidates[1]})"
    )


def _parse_year(parts, line_number):
    if len(parts) != 3:
        raise ValueError(
            "SET_APPRAISAL_YEAR must use "
            f"SET_APPRAISAL_YEAR|year|YYYY-MM-DD (line {line_number})"
        )
    try:
        year = int(parts[1])
        cutoff_date = date.fromisoformat(parts[2])
    except ValueError:
        raise ValueError(
            f"Invalid appraisal year or cutoff date (line {line_number})"
        )
    if (
        len(parts[1]) != 4
        or not 1 <= year <= 9998
        or cutoff_date.isoformat() != parts[2]
        or cutoff_date.year != year
    ):
        raise ValueError(
            f"Invalid appraisal year or cutoff date (line {line_number})"
        )
    return year, cutoff_date


def _parse_company_multiplier(parts, line_number):
    if len(parts) != 2:
        raise ValueError(
            "SET_COMPANY_MULTIPLIER must use "
            f"SET_COMPANY_MULTIPLIER|multiplier (line {line_number})"
        )
    try:
        multiplier = float(parts[1])
    except ValueError:
        raise ValueError(f"Company multiplier must be numeric (line {line_number})")
    if not 0.8 <= multiplier <= 1.2:
        raise ValueError(
            f"Company multiplier must be between 0.8 and 1.2 "
            f"(line {line_number})"
        )
    return multiplier


def _parse_appeal(parts, line_number):
    if len(parts) < 5 or len(parts) % 2 == 0 or not all(parts[1:]):
        raise ValueError(
            "APPEAL must use "
            "APPEAL|appeal_id|emp_id|goal_id|new_rating"
            "[|goal_id|new_rating] "
            f"(line {line_number})"
        )
    appeal_id, employee_id = parts[1:3]
    new_ratings = {}
    for index in range(3, len(parts), 2):
        goal_id = parts[index]
        if goal_id in new_ratings:
            raise ValueError(f"APPEAL repeats goal {goal_id!r} (line {line_number})")
        try:
            rating = int(parts[index + 1])
        except ValueError:
            raise ValueError(f"APPEAL rating must be an integer (line {line_number})")
        if rating not in range(1, 6):
            raise ValueError(f"APPEAL rating must be 1 through 5 (line {line_number})")
        new_ratings[goal_id] = rating
    return appeal_id, employee_id, new_ratings


class AppraisalWorkflow:
    def __init__(self, commands_path, output_dir):
        self.commands_path = Path(commands_path)
        self.command_dir = self.commands_path.parent
        self.output_dir = Path(output_dir)
        self.appraisal_year = None
        self.cutoff_date = None
        self.company_multiplier = None
        self.data = None
        self.grade_bands_path = None
        self.scores = None
        self.eligibility = None
        self.final_results = None
        self.compensation = {}
        self.promoted_employee_ids = set()
        self.promoted_grades = {}
        self.distribution_output = []
        self.appeal_output = []
        self.print_number = 0
        self.pending_appeal = None
        self.appeal_ids = set()

    def _load(self, parts, line_number):
        if len(parts) not in {6, 7}:
            raise ValueError(
                "LOAD must specify employees, goals, ratings, bands, units, "
                "and optionally a competency catalog "
                f"(line {line_number})"
            )
        if self.appraisal_year is None or self.company_multiplier is None:
            raise ValueError(
                "SET_APPRAISAL_YEAR and SET_COMPANY_MULTIPLIER must precede "
                f"LOAD (line {line_number})"
            )
        paths = [
            _resolve_load_path(self.command_dir, filename)
            for filename in parts[1:]
        ]
        if len(paths) < 5:
            raise ValueError(
                f"LOAD input filenames cannot be empty (line {line_number})"
            )
        catalog_path = (
            paths[5]
            if len(paths) == 6
            else paths[2].with_name("competency_catalog.json")
        )
        self.data = load_official_data(
            *paths[:5],
            appraisal_cutoff_date=self.cutoff_date,
            competency_catalog_path=catalog_path,
        )
        self.grade_bands_path = paths[3]

    def _run_appraisal(self):
        if self.data is None:
            raise ValueError("LOAD must precede RUN_APPRAISAL")
        employees, goals, ratings, statuses, _, _ = self.data
        scorable_employees = {
            employee_id: employee
            for employee_id, employee in employees.items()
            if statuses.get(employee_id) not in INVALID_STATUSES
        }
        self.scores = calculate_raw_scores(
            scorable_employees, goals, ratings
        )
        self.eligibility = get_eligibility_results(
            employees, self.appraisal_year, self.cutoff_date
        )
        self.eligibility.update(statuses)
        self.final_results = distribute_ratings(
            employees,
            self.scores,
            self.eligibility,
            self.appraisal_year,
        )
        self._refresh_compensation()

    def _refresh_compensation(self):
        employees, _, _, _, _, budgets = self.data
        self.promoted_employee_ids = select_promotions(
            employees,
            self.final_results,
            self.scores,
            self.eligibility,
            self.cutoff_date,
            grade_order=list(self.data[4]),
        )
        self.promoted_grades = {
            employee_id: next_grade_in_order(
                employees[employee_id].grade,
                self.data[4],
            )
            for employee_id in self.promoted_employee_ids
        }
        scaled_rates = calculate_scaled_increment_rates(
            employees,
            self.final_results,
            self.appraisal_year,
            budgets,
            self.promoted_employee_ids,
            self.cutoff_date,
            proration_through_cutoff=True,
            annualize_cost=True,
            grade_bands=self.data[4],
            new_grades=self.promoted_grades,
        )
        self.compensation = {}
        for employee_id, result in self.final_results.items():
            if result["final_rating"] is None:
                continue
            employee = employees[employee_id]
            self.compensation[employee_id] = calculate_compensation(
                employee,
                result["final_rating"],
                self.appraisal_year,
                grade_bands_path=self.grade_bands_path,
                new_grade=self.promoted_grades.get(employee_id),
                is_promotion=employee_id in self.promoted_employee_ids,
                company_multiplier=self.company_multiplier,
                increment_rate_override=scaled_rates[employee_id],
                appraisal_cutoff_date=self.cutoff_date,
                proration_through_cutoff=True,
            )

    def _appeal(self, parts, line_number):
        if self.final_results is None:
            raise ValueError(f"RUN_APPRAISAL must precede APPEAL (line {line_number})")
        if self.pending_appeal is not None:
            raise ValueError(
                f"RERUN_UNIT must follow the pending appeal before another "
                f"APPEAL (line {line_number})"
            )
        try:
            appeal_id, employee_id, new_ratings = _parse_appeal(
                parts, line_number
            )
        except ValueError as error:
            print(f"APPEAL rejected: {error}")
            return
        if appeal_id in self.appeal_ids:
            print(f"APPEAL {appeal_id} rejected: duplicate appeal ID")
            return
        employees, goals, ratings, statuses, _, _ = self.data
        scorable_employees = {
            candidate_id: employee
            for candidate_id, employee in employees.items()
            if statuses.get(candidate_id) not in INVALID_STATUSES
        }
        try:
            process_appeal(
                scorable_employees,
                goals,
                ratings,
                self.scores,
                self.final_results,
                self.eligibility,
                employee_id,
                list(new_ratings),
                self.appraisal_year,
                new_ratings=new_ratings,
            )
        except ValueError as error:
            print(f"APPEAL {appeal_id} rejected: {error}")
            return
        self.appeal_ids.add(appeal_id)
        self.pending_appeal = {
            "appeal_id": appeal_id,
            "employee_id": employee_id,
        }
        print(f"APPEAL {appeal_id} accepted")

    def _rerun_unit(self, parts, line_number):
        if len(parts) != 2 or not parts[1]:
            raise ValueError(f"RERUN_UNIT must specify one unit (line {line_number})")
        if self.final_results is None:
            raise ValueError(f"RUN_APPRAISAL must precede RERUN_UNIT (line {line_number})")

        unit = parts[1]
        employees, goals, ratings, statuses, _, _ = self.data
        pools, unit_members = build_distribution_pools(
            employees, self.eligibility
        )
        target_pool = next((pool for pool in pools if unit in pool), None)
        if target_pool is None:
            if unit not in {employee.business_unit for employee in employees.values()}:
                raise ValueError(f"Unknown unit in RERUN_UNIT: {unit}")
            target_pool = [unit]
            unit_members.setdefault(unit, [])
        target_ids = {
            employee_id
            for target_unit in target_pool
            for employee_id in unit_members[target_unit]
        }

        if self.pending_appeal is not None:
            appealed_employee = self.pending_appeal["employee_id"]
            if appealed_employee not in target_ids:
                raise ValueError(
                    f"RERUN_UNIT|{unit} does not include pending appeal "
                    f"employee {appealed_employee}"
                )

        scorable_employees = {
            employee_id: employee
            for employee_id, employee in employees.items()
            if statuses.get(employee_id) not in INVALID_STATUSES
        }
        updated_scores = calculate_raw_scores(scorable_employees, goals, ratings)
        updated_results = distribute_ratings(
            employees,
            updated_scores,
            self.eligibility,
            self.appraisal_year,
        )
        changed_ids = []
        for employee_id in target_ids:
            before = self.final_results[employee_id]["final_rating"]
            after = updated_results[employee_id]["final_rating"]
            self.final_results[employee_id] = updated_results[employee_id]
            if before != after:
                changed_ids.append((employee_id, before, after))
        self.scores = updated_scores

        if self.pending_appeal is not None:
            pool_name = "+".join(target_pool)
            for employee_id, before, after in sorted(changed_ids):
                self.appeal_output.append({
                    "appeal_id": self.pending_appeal["appeal_id"],
                    "unit_or_pool": pool_name,
                    "emp_id": employee_id,
                    "rating_before": before,
                    "rating_after": after,
                })
            self.pending_appeal = None

        self._refresh_compensation()

    def _letter_rows(self):
        employees = self.data[0]
        rows = []
        for employee_id in sorted(employees):
            employee = employees[employee_id]
            status = self.data[3].get(employee_id)
            if status is None:
                status = (
                    "OK"
                    if self.eligibility[employee_id] == "ELIGIBLE"
                    else "NOT_ELIGIBLE"
                )
            result = self.final_results[employee_id]
            score = self.scores.get(employee_id, {})
            compensation = self.compensation.get(employee_id, {})
            final_rating = result["final_rating"]
            rows.append({
                "emp_id": employee_id,
                "unit": employee.business_unit,
                "eligible": str(status == "OK").lower(),
                "raw_score": (
                    f"{score['raw_score']:.2f}" if score else ""
                ),
                "goal_score": (
                    f"{score['goal_score']:.2f}" if score else ""
                ),
                "final_rating": "" if final_rating is None else final_rating,
                "increment_pct": (
                    f"{compensation['increment_rate'] * 100:.1f}"
                    if compensation else ""
                ),
                "pro_rated": (
                    str(compensation["proration"] < 1).lower()
                    if compensation else "false"
                ),
                "revised_basic": (
                    f"{compensation['revised_salary']:.2f}"
                    if compensation else ""
                ),
                "lump_sum": (
                    f"{compensation['lump_sum']:.2f}"
                    if compensation else ""
                ),
                "variable_payout": (
                    f"{compensation['variable_pay']:.2f}"
                    if compensation else ""
                ),
                "promoted": str(
                    employee_id in self.promoted_employee_ids
                ).lower(),
                "new_grade": self.promoted_grades.get(employee_id, ""),
                "pip": str(compensation.get("on_pip", False)).lower(),
                "status_code": status,
            })
        return rows

    def execute(self):
        with self.commands_path.open("r", encoding="utf-8-sig") as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [part.strip() for part in line.split("|")]
                command = parts[0]
                if command == "SET_APPRAISAL_YEAR":
                    if self.appraisal_year is not None:
                        raise ValueError("SET_APPRAISAL_YEAR may be set only once")
                    self.appraisal_year, self.cutoff_date = _parse_year(
                        parts, line_number
                    )
                elif command == "SET_COMPANY_MULTIPLIER":
                    if self.company_multiplier is not None:
                        raise ValueError(
                            "SET_COMPANY_MULTIPLIER may be set only once"
                        )
                    self.company_multiplier = _parse_company_multiplier(
                        parts, line_number
                    )
                elif command == "LOAD":
                    if self.data is not None:
                        raise ValueError("LOAD may be specified only once")
                    self._load(parts, line_number)
                elif command == "RUN_APPRAISAL":
                    if len(parts) != 1:
                        raise ValueError(
                            f"RUN_APPRAISAL takes no arguments (line {line_number})"
                        )
                    self._run_appraisal()
                elif command == "APPEAL":
                    self._appeal(parts, line_number)
                elif command == "RERUN_UNIT":
                    self._rerun_unit(parts, line_number)
                elif command == "PRINT_DISTRIBUTION":
                    if len(parts) != 2 or parts[1] != "ALL":
                        raise ValueError(
                            "PRINT_DISTRIBUTION must use "
                            f"PRINT_DISTRIBUTION|ALL (line {line_number})"
                        )
                    if self.final_results is None:
                        raise ValueError(
                            f"RUN_APPRAISAL must precede PRINT_DISTRIBUTION "
                            f"(line {line_number})"
                        )
                    self.print_number += 1
                    self.distribution_output.extend(
                        distribution_rows(
                            self.data[0],
                            self.eligibility,
                            self.final_results,
                            self.print_number,
                        )
                    )
                    write_distribution(
                        self.output_dir / "distribution.csv",
                        self.distribution_output,
                    )
                elif command == "PRINT_LETTERS":
                    if len(parts) != 2 or parts[1] != "ALL":
                        raise ValueError(
                            "PRINT_LETTERS must use PRINT_LETTERS|ALL "
                            f"(line {line_number})"
                        )
                    if self.final_results is None:
                        raise ValueError(
                            f"RUN_APPRAISAL must precede PRINT_LETTERS "
                            f"(line {line_number})"
                        )
                    write_letters(
                        self.output_dir / "letters.csv",
                        self._letter_rows(),
                    )
                else:
                    raise ValueError(
                        f"Unknown command {command!r} (line {line_number})"
                    )

        if self.pending_appeal is not None:
            raise ValueError(
                f"Appeal {self.pending_appeal['appeal_id']} was not followed "
                "by RERUN_UNIT"
            )
        if self.data is None:
            raise ValueError("Command file is missing LOAD")
        if self.final_results is None:
            raise ValueError("Command file is missing RUN_APPRAISAL")

        write_appeal_changes(
            self.output_dir / "appeal_changes.csv",
            self.appeal_output,
        )
        for employee_id, new_grade in self.promoted_grades.items():
            employee = self.data[0][employee_id]
            employee.grade = new_grade
            employee.months_in_grade = 0
        return self


def run_commands(commands_path, output_dir):
    return AppraisalWorkflow(commands_path, output_dir).execute()
