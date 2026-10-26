
def calculate_raw_scores(employees, goals, ratings):
    """Calculate goal, competency, and raw weighted scores."""

    # Store each employee's manager ratings for their goals
    goal_ratings = {}
    competency_ratings = {}

    for rating in ratings:
        employee_id = rating.employee_id

        if rating.item_type == "GOAL":
            goal_ratings[(employee_id, rating.item_id)] = (
                rating.manager_rating
            )

        elif rating.item_type == "COMPETENCY":
            competency_ratings.setdefault(employee_id, []).append(
                rating.manager_rating
            )

    # Calculate weighted goal score for each employee
    goal_scores = {}

    for employee_id in employees:
        total = 0.0

        for goal in goals:
            if goal.employee_id == employee_id:
                manager_rating = goal_ratings[
                    (employee_id, goal.goal_id)
                ]
                total += manager_rating * goal.weight / 100

        goal_scores[employee_id] = total

    # Calculate competency average and final raw score
    results = {}

    for employee_id in employees:
        competency_values = competency_ratings.get(employee_id, [])

        if not competency_values:
            raise ValueError(
                f"{employee_id}: no competency ratings found"
            )

        competency_score = (
            sum(competency_values) / len(competency_values)
        )

        goal_score = goal_scores[employee_id]

        raw_score = (
            goal_score * 0.70
            + competency_score * 0.30
        )

        results[employee_id] = {
            "goal_score": goal_score,
            "competency_score": competency_score,
            "raw_score": raw_score,
        }

    return results
