from pathlib import Path

from src.calibration import distribute_ratings
from src.scoring import calculate_raw_scores


def process_appeal(
    employees,
    goals,
    ratings,
    scores,
    final_results,
    eligibility,
    employee_id,
    goal_ids,
    appraisal_year,
    new_ratings=None,
):
    """Apply a valid appeal and recalibrate ratings from the current scores."""
    if employee_id not in employees:
        raise ValueError(f"Appeal references unknown employee: {employee_id}")
    if eligibility.get(employee_id) != "ELIGIBLE":
        raise ValueError("An ineligible employee cannot appeal")
    if not 1 <= len(goal_ids) <= 2 or len(set(goal_ids)) != len(goal_ids):
        raise ValueError("An appeal must specify one or two distinct goals")

    owned_goal_ids = {
        goal.goal_id for goal in goals
        if goal.employee_id == employee_id
    }
    if any(goal_id not in owned_goal_ids for goal_id in goal_ids):
        raise ValueError("Appeal references a goal not assigned to employee")

    ratings_by_goal = {
        rating.item_id: rating for rating in ratings
        if rating.employee_id == employee_id
        and rating.item_type == "GOAL"
    }
    requested_ratings = new_ratings or {}
    for goal_id in goal_ids:
        rating = ratings_by_goal.get(goal_id)
        if rating is None:
            raise ValueError(f"Missing manager rating for goal {goal_id}")
        requested = requested_ratings.get(goal_id, rating.manager_rating + 1)
        if (
            not isinstance(requested, int)
            or requested <= rating.manager_rating
            or requested > rating.manager_rating + 1
            or requested > 5
        ):
            raise ValueError(
                f"Manager rating for goal {goal_id} may increase by at "
                "most one point"
            )

    for goal_id in goal_ids:
        ratings_by_goal[goal_id].manager_rating = requested_ratings.get(
            goal_id, ratings_by_goal[goal_id].manager_rating + 1
        )

    updated_scores = calculate_raw_scores(employees, goals, ratings)
    updated_results = distribute_ratings(
        employees,
        updated_scores,
        eligibility,
        appraisal_year,
    )
    changed_employee_ids = {
        candidate_id
        for candidate_id, result in updated_results.items()
        if final_results[candidate_id]["final_rating"]
        != result["final_rating"]
    }

    return updated_scores, updated_results, changed_employee_ids


def load_appeal_commands(commands_path):
    """Read APPEAL|employee_id|goal_id[,goal_id] command lines."""
    commands = []
    with Path(commands_path).open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            parts = [part.strip() for part in line.split("|")]
            if not parts or parts[0] != "APPEAL":
                continue
            if len(parts) != 3 or not parts[1] or not parts[2]:
                raise ValueError(
                    "APPEAL must use "
                    "APPEAL|employee_id|goal_id[,goal_id] "
                    f"(line {line_number})"
                )
            goal_ids = [goal_id.strip() for goal_id in parts[2].split(",")]
            if any(not goal_id for goal_id in goal_ids):
                raise ValueError(
                    f"APPEAL contains an empty goal ID (line {line_number})"
                )
            commands.append((parts[1], goal_ids))

    return commands