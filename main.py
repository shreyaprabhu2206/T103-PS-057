
import argparse
from pathlib import Path

from src.calibration import (
    get_eligibility_results,
    distribute_ratings,
    load_appraisal_settings,
)
from src.validation import load_and_validate
from src.scoring import calculate_raw_scores
from src.compensation import (
    calculate_compensation,
    calculate_scaled_increment_rates,
    load_company_multiplier,
    load_grade_bands,
    load_increment_budgets,
)
from src.promotion import next_grade_in_order, select_promotions
from src.appeals import load_appeal_commands, process_appeal
from src.workflow import run_commands


def _run_legacy():
    input_dir = Path(__file__).parent / "data" / "input"

    try:
        appraisal_year, appraisal_cutoff_date = load_appraisal_settings(
            input_dir / "commands.csv"
        )
        company_multiplier = load_company_multiplier(
            input_dir / "commands.csv"
        )

        # 1. Load and validate input data
        employees, goals, ratings = load_and_validate(input_dir)

        print("Input validation successful!")
        print(f"Employees loaded: {len(employees)}")
        print(f"Goals loaded: {len(goals)}")
        print(f"Ratings loaded: {len(ratings)}")

        # 2. Calculate raw appraisal scores
        scores = calculate_raw_scores(
            employees, goals, ratings
        )

        print("\n--- RAW APPRAISAL SCORES ---")

        for employee_id, result in sorted(scores.items()):
            print(
                f"{employee_id} | "
                f"Goal: {result['goal_score']:.2f} | "
                f"Competency: {result['competency_score']:.2f} | "
                f"Raw: {result['raw_score']:.2f}"
            )

        # 3. Check eligibility
        eligibility = get_eligibility_results(
            employees, appraisal_year, appraisal_cutoff_date
        )

        print(f"\n--- ELIGIBILITY RESULTS ({appraisal_year}) ---")

        for employee_id in sorted(employees):
            print(
                f"{employee_id} | "
                f"Joining date: {employees[employee_id].joining_date} | "
                f"Status: {eligibility[employee_id]}"
            )

        # 4. Assign final bell-curve ratings
        final_results = distribute_ratings(
            employees,
            scores,
            eligibility,
            appraisal_year
        )

        for employee_id, goal_ids in load_appeal_commands(
            input_dir / "commands.csv"
        ):
            previous_ratings = {
                candidate_id: result["final_rating"]
                for candidate_id, result in final_results.items()
            }
            scores, final_results, changed_employee_ids = process_appeal(
                employees,
                goals,
                ratings,
                scores,
                final_results,
                eligibility,
                employee_id,
                goal_ids,
                appraisal_year,
            )
            print(
                f"\n--- APPEAL RESULT: {employee_id} ---"
            )
            if changed_employee_ids:
                for changed_id in sorted(changed_employee_ids):
                    print(
                        f"{changed_id} | Final rating: "
                        f"{previous_ratings[changed_id]} -> "
                        f"{final_results[changed_id]['final_rating']}"
                    )
            else:
                print("No employees' final ratings changed")

        grade_bands_path = input_dir / "grade_bands.csv"
        grade_bands = load_grade_bands(grade_bands_path)
        grade_order = list(grade_bands)
        promoted_employee_ids = select_promotions(
            employees,
            final_results,
            scores,
            eligibility,
            appraisal_cutoff_date,
            grade_order=grade_order,
        )
        promoted_grades = {
            employee_id: next_grade_in_order(
                employees[employee_id].grade,
                grade_order,
            )
            for employee_id in promoted_employee_ids
        }
        scaled_increment_rates = calculate_scaled_increment_rates(
            employees,
            final_results,
            appraisal_year,
            load_increment_budgets(input_dir / "budgets.csv"),
            promoted_employee_ids,
            appraisal_cutoff_date,
            grade_bands=grade_bands,
            new_grades=promoted_grades,
        )

        print(
            f"\n--- FINAL BELL-CURVE RATINGS "
            f"({appraisal_year}) ---"
        )

        for employee_id in sorted(employees):
            result = final_results[employee_id]

            if result["final_rating"] is None:
                print(
                    f"{employee_id} | NOT_ELIGIBLE "
                    "| No final rating"
                )
            else:
                print(
                    f"{employee_id} | "
                    f"Pool: {result['pool']} | "
                    f"Rank: {result['rank']} | "
                    f"Final rating: {result['final_rating']}"
                )

        # 5. Calculate compensation
        print("\n--- COMPENSATION REPORT ---")

        for employee_id in sorted(employees):
            result = final_results[employee_id]

            if result["final_rating"] is None:
                print(
                    f"{employee_id} | "
                    "NOT_ELIGIBLE | No increment"
                )
                continue

            employee = employees[employee_id]

            compensation = calculate_compensation(
                employee,
                result["final_rating"],
                appraisal_year,
                grade_bands_path=grade_bands_path,
                new_grade=promoted_grades.get(employee_id),
                is_promotion=employee_id in promoted_employee_ids,
                company_multiplier=company_multiplier,
                increment_rate_override=scaled_increment_rates[employee_id],
                appraisal_cutoff_date=appraisal_cutoff_date,
            )

            print(
                f"{employee_id} | "
                f"Rating: {compensation['final_rating']} | "
                f"Promotion: "
                f"{'YES' if employee_id in promoted_employee_ids else 'NO'} | "
                f"Increment: "
                f"{compensation['increment_rate'] * 100:.0f}% | "
                f"Proration: "
                f"{compensation['proration'] * 100:.1f}% | "
                f"Current salary: "
                f"Rs.{compensation['current_salary']} | "
                f"Revised salary: "
                f"Rs.{compensation['revised_salary']}"
                f" | Variable pay: Rs.{compensation['variable_pay']}"
            )

        for employee_id, new_grade in promoted_grades.items():
            employees[employee_id].grade = new_grade
            employees[employee_id].months_in_grade = 0

    except (ValueError, OSError, KeyError) as error:
        print(f"INPUT OR SCORING ERROR: {error}")
        raise SystemExit(1)


def main():
    project_dir = Path(__file__).parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--commands",
        type=Path,
        help="Run the ordered PS-057 command file at this path",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_dir / "output",
        help="Directory for generated CSV reports",
    )
    args = parser.parse_args()

    commands_path = args.commands
    if commands_path is None:
        default_commands = project_dir / "commands.txt"
        if default_commands.is_file():
            commands_path = default_commands

    if commands_path is None:
        _run_legacy()
        return

    try:
        workflow = run_commands(commands_path, args.output_dir)
        print(
            f"Command file completed. Employees loaded: "
            f"{len(workflow.data[0])}. "
            f"Reports: {args.output_dir}"
        )
    except (ValueError, OSError, KeyError) as error:
        print(f"INPUT OR APPRAISAL ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
