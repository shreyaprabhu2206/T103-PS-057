
from pathlib import Path

from src.calibration import (
    get_eligibility_results,
    distribute_ratings,
)
from src.validation import load_and_validate
from src.scoring import calculate_raw_scores
from src.compensation import calculate_compensation


APPRAISAL_YEAR = 2025


def main():
    input_dir = Path(__file__).parent / "data" / "input"

    try:
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
            employees, APPRAISAL_YEAR
        )

        print(f"\n--- ELIGIBILITY RESULTS ({APPRAISAL_YEAR}) ---")

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
            APPRAISAL_YEAR
        )

        print(
            f"\n--- FINAL BELL-CURVE RATINGS "
            f"({APPRAISAL_YEAR}) ---"
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
                APPRAISAL_YEAR
            )

            print(
                f"{employee_id} | "
                f"Rating: {compensation['final_rating']} | "
                f"Increment: "
                f"{compensation['increment_rate'] * 100:.0f}% | "
                f"Proration: "
                f"{compensation['proration'] * 100:.1f}% | "
                f"Current salary: "
                f"Rs.{compensation['current_salary']} | "
                f"Revised salary: "
                f"Rs.{compensation['revised_salary']}"
            )

    except (ValueError, OSError, KeyError) as error:
        print(f"INPUT OR SCORING ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
