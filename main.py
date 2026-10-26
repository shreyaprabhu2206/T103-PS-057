
from pathlib import Path
from src.calibration import get_eligibility_results
from src.validation import load_and_validate
from src.scoring import calculate_raw_scores
from src.calibration import distribute_ratings

def main():
    input_dir = Path(__file__).parent / "data" / "input"

    try:
        employees, goals, ratings = load_and_validate(input_dir)

        print("Input validation successful!")
        print(f"Employees loaded: {len(employees)}")
        print(f"Goals loaded: {len(goals)}")
        print(f"Ratings loaded: {len(ratings)}")

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

            eligibility = get_eligibility_results(
            employees, 2025
        )

        print("\n--- ELIGIBILITY RESULTS (2025) ---")

        for employee_id in sorted(employees):
            print(
                f"{employee_id} | "
                f"Joining date: {employees[employee_id].joining_date} | "
                f"Status: {eligibility[employee_id]}"
            )
        
        final_results = distribute_ratings(
            employees,
            scores,
            eligibility,
            2025
        )

        print("\n--- FINAL BELL-CURVE RATINGS (2025) ---")

        for employee_id in sorted(employees):
            result = final_results[employee_id]

            if result["final_rating"] is None:
                print(
                    f"{employee_id} | NOT_ELIGIBLE "
                    f"| No final rating"
                )
            else:
                print(
                    f"{employee_id} | "
                    f"Pool: {result['pool']} | "
                    f"Rank: {result['rank']} | "
                    f"Final rating: {result['final_rating']}"
                )

    except (ValueError, OSError, KeyError) as error:
        print(f"INPUT OR SCORING ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
