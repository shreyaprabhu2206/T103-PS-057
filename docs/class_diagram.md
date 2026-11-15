# Implemented Class and Module Diagram

The diagram distinguishes the implemented data classes and workflow class from
the processing modules. Scores, calibration results, and compensation results
are dictionaries in the implementation; they are not separate model classes.

```mermaid
classDiagram
    class Employee {
        +employee_id: str
        +business_unit: str
        +grade: str
        +basic_salary: float
        +joining_date: date
        +manager_id: str
        +current_role_band: str
        +grade_start_date: date
        +previous_final_rating: Optional[int]
        +months_in_grade: Optional[int]
    }

    class Goal {
        +employee_id: str
        +goal_id: str
        +goal_name: str
        +weight: int
    }

    class Rating {
        +employee_id: str
        +item_type: str
        +item_id: str
        +self_rating: int
        +manager_rating: int
    }

    class AppraisalWorkflow {
        +commands_path: Path
        +output_dir: Path
        +pending_appeal: dict or None
        +execute()
        -_load(parts, line_number)
        -_run_appraisal()
        -_appeal(parts, line_number)
        -_rerun_unit(parts, line_number)
        -_refresh_compensation(final_results, scores)
    }

    class MainModule {
        <<module>>
        +main()
    }
    class OfficialDataModule {
        <<module>>
        +load_official_data(...)
    }
    class ScoringModule {
        <<module>>
        +calculate_raw_scores(...)
    }
    class CalibrationModule {
        <<module>>
        +get_eligibility_results(...)
        +distribute_ratings(...)
        +build_distribution_pools(...)
    }
    class AppealsModule {
        <<module>>
        +process_appeal(...)
    }
    class PromotionModule {
        <<module>>
        +select_promotions(...)
    }
    class CompensationModule {
        <<module>>
        +calculate_scaled_increment_rates(...)
        +calculate_compensation(...)
    }
    class ReportsModule {
        <<module>>
        +write_distribution(...)
        +write_letters(...)
        +write_appeal_changes(...)
    }

    Employee "1" --> "0..*" Goal : assigned
    Employee "1" --> "0..*" Rating : has
    MainModule ..> AppraisalWorkflow : starts via run_commands
    AppraisalWorkflow ..> OfficialDataModule : LOAD
    AppraisalWorkflow ..> ScoringModule : calculate and refresh scores
    AppraisalWorkflow ..> CalibrationModule : initial and unit reruns
    AppraisalWorkflow ..> AppealsModule : validate and apply appeal
    AppraisalWorkflow ..> PromotionModule : select candidates
    AppraisalWorkflow ..> CompensationModule : recalculate pay
    AppraisalWorkflow ..> ReportsModule : write CSV reports
```

`commands.txt` is a line-oriented input read by `AppraisalWorkflow.execute()`;
it is not represented as a Python data class. The workflow processes settings,
`LOAD`, `RUN_APPRAISAL`, `APPEAL`, `RERUN_UNIT`, and print commands in file
order. The current working assumption advances a promotion to the next grade
in `grade_bands.csv` order; this progression is awaiting Capstone confirmation.
After a successful promotion, the confirmed rule sets `months_in_grade` to
zero. See the [decision log](decision_log.md).
