# UML Class Diagram

## Purpose

The class diagram represents the main data models and processing components of the Performance Appraisal and Bell-Curve Normalisation system. It shows how employee details, goals, ratings, appraisal scores, calibration and compensation are connected.

## Class Diagram

```mermaid
classDiagram
    class Employee {
        +String employee_id
        +String name
        +String business_unit
        +String grade
        +float basic_salary
        +Date joining_date
        +float previous_final_rating
    }

    class Goal {
        +String goal_id
        +String employee_id
        +String description
        +float weight
    }

    class Rating {
        +String employee_id
        +String item_id
        +String item_type
        +float self_rating
        +float manager_rating
    }

    class AppraisalResult {
        +String employee_id
        +float goal_score
        +float competency_score
        +float raw_score
        +int final_rating
    }

    class Validation {
        +validate_employees()
        +validate_goals()
        +validate_ratings()
    }

    class Scoring {
        +calculate_goal_score()
        +calculate_competency_score()
        +calculate_raw_score()
    }

    class Calibration {
        +check_eligibility()
        +pool_small_business_units()
        +assign_final_ratings()
    }

    class Compensation {
        +calculate_increment()
        +calculate_revised_salary()
        +calculate_variable_pay()
    }

    Employee "1" --> "0..*" Goal : has
    Employee "1" --> "0..*" Rating : receives
    Employee "1" --> "0..1" AppraisalResult : gets
    Goal ..> Rating : rated through
    Validation ..> Employee : validates
    Validation ..> Goal : validates
    Validation ..> Rating : validates
    Scoring ..> Rating : uses
    Scoring ..> Goal : uses
    Scoring ..> AppraisalResult : creates
    Calibration ..> AppraisalResult : normalises
    Compensation ..> AppraisalResult : uses
    Compensation ..> Employee : uses
```

## Explanation

1. **Employee:** Stores employee details such as ID, name, business unit, grade, salary and joining date.
2. **Goal:** Stores the goals assigned to each employee and their weights.
3. **Rating:** Stores self-ratings and manager ratings for goals and competencies.
4. **AppraisalResult:** Stores the calculated goal score, competency score, raw score and final rating.
5. **Validation:** Checks whether the input data is complete and follows the required rules.
6. **Scoring:** Calculates goal scores, competency scores and the final raw appraisal score.
7. **Calibration:** Applies eligibility rules and bell-curve normalisation to assign final ratings.
8. **Compensation:** Calculates increments, revised salaries and variable pay based on appraisal results.

## Note

This is the design-level class diagram. Some components, such as `AppraisalResult` and the processing classes, represent planned logical responsibilities and may be implemented as Python functions or modules rather than separate classes.