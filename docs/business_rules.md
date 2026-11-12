# Business Rule Register

## Project: Performance Appraisal and Bell-Curve Normalisation with Increment Bands

**Project ID:** T103-PS-057  
**Team:** T103  
**Section:** ISE D  
**Technology:** Python 3.10+

---

## 1. Employee and Input Validation Rules

| Rule ID | Rule Name | Description |
|---|---|---|
| BR-01 | Employee ID Validation | Each employee must have a unique employee ID so that employee records can be identified correctly. |
| BR-02 | Employee Data Validation | All important employee details, such as business unit, grade, basic salary, joining date and manager ID, must be provided. |
| BR-03 | Grade Validation | The employee's grade should be one of the supported grades, from G1 to G7. |
| BR-04 | Salary Validation | The basic salary entered for an employee must be a valid positive amount. |
| BR-05 | Goal Weight Validation | The total weight assigned to an employee's goals must add up to exactly 100%. If it does not, the system should return `INVALID_WEIGHTS`. |
| BR-06 | Rating Range Validation | Both self-ratings and manager ratings must be within the range of 1 to 5. |
| BR-07 | Missing Rating Validation | The system should check that every required goal and competency has a manager rating before calculating the appraisal score. |

## 2. Appraisal Scoring Rules

| Rule ID | Rule Name | Description |
|---|---|---|
| BR-08 | Goal Score Calculation | The goal score is calculated using the manager's ratings for each goal along with the weight assigned to that goal. |
| BR-09 | Competency Score Calculation | The competency score is calculated by taking the average of the manager's ratings for the employee's competencies. |
| BR-10 | Raw Score Calculation | The final raw appraisal score is calculated by giving 70% weight to the goal score and 30% weight to the competency score. |
| BR-11 | Manager Rating Usage | Manager ratings are considered when calculating the employee's raw appraisal score. |
| BR-12 | Self Rating Usage | Self-ratings are kept for comparison with manager ratings and for preparing rating gap reports. They are not used in the raw score calculation. |

## 3. Eligibility Rules

| Rule ID | Rule Name | Description |
|---|---|---|
| BR-13 | Eligibility Cut-off | Employees who join after 30 September of the appraisal year will not be considered eligible for that appraisal cycle. |
| BR-14 | Eligible Joiners | Employees who join on or before 30 September can be considered for the appraisal cycle, subject to the other eligibility conditions. |
| BR-15 | Prorated Increment | Employees who join between 1 April and 30 September will receive an increment based on the number of completed months they have worked during the appraisal cycle. |

## 4. Bell-Curve Normalisation Rules

| Rule ID | Rule Name | Description |
|---|---|---|
| BR-16 | Business Unit Distribution | The system should distribute final performance ratings within each business unit according to the specified bell-curve percentages. |
| BR-17 | Rating 5 Distribution | The top 10% of eligible employees should receive a rating of 5. |
| BR-18 | Rating 4 Distribution | The next 20% of eligible employees should receive a rating of 4. |
| BR-19 | Rating 3 Distribution | The next 50% of eligible employees should receive a rating of 3. |
| BR-20 | Rating 2 Distribution | The next 15% of eligible employees should receive a rating of 2. |
| BR-21 | Rating 1 Distribution | The bottom 5% of eligible employees should receive a rating of 1. |
| BR-22 | Small Business Unit Pooling | If a business unit has fewer than 10 eligible employees, it should be combined with the next business unit alphabetically until the combined group has at least 10 employees. |
| BR-23 | Distribution Rounding | When calculating the number of employees in each rating category, fractional values should be rounded down. Any remaining employees should be added to rating 3. |
| BR-24 | Tie-Breaking | If two or more employees have the same score, the system should compare their raw scores, goal scores, length of service and employee IDs, in that order, to decide their ranking. |
| BR-25 | Ineligible Employee Exclusion | Employees who are not eligible for the appraisal cycle should be excluded from the bell-curve distribution. |

**Implementation assumption (not an official rule):** if the final
alphabetical pool still has fewer than 10 eligible employees and no next unit
is available, process it as a residual pool using the ordinary floor bucket
sizes and add unassigned employees to rating 3. Tests cover residual sizes 1,
5, and 9.

## 5. Increment Rules

| Rule ID | Rule Name | Description |
|---|---|---|
| BR-26 | Rating-Based Increment | The increment percentage depends on the final rating: 14% for rating 5, 10% for rating 4, 6% for rating 3, 2% for rating 2 and 0% for rating 1. |
| BR-27 | Revised Basic Salary | The revised basic salary is calculated by adding the applicable increment amount to the employee's current basic salary. |
| BR-28 | Salary Rounding | After calculating the revised salary, the amount should be rounded up to the next ₹100. |
| BR-29 | Minimum Increment Floor | Eligible employees with a rating of 3 or above should receive a revised basic salary of at least ₹25,000 per month if their calculated salary is below that amount. |
| BR-30 | Ineligible Employee Increment | Employees who are not eligible for the appraisal cycle should not receive an increment during that cycle. |

## 6. Promotion Rules

| Rule ID | Rule Name | Description |
|---|---|---|
| BR-31 | Promotion Eligibility – Rating 5 | An employee with a rating of 5 can be considered for promotion if they have completed at least 24 months in their current grade. |
| BR-32 | Promotion Eligibility – Rating 4 | An employee with a rating of 4 can be considered for promotion if they have completed at least 36 months in their current grade. |
| BR-33 | Promotion Increment | Employees selected for promotion will receive an additional 5% increment. |
| BR-34 | Promotion Limit | The number of promotions in a cycle should not exceed 8% of the eligible business unit headcount, rounded up to the next whole number. |
| BR-35 | Promotion Selection | If more employees qualify for promotion than the available limit, those with higher raw appraisal scores should be given preference. |

## 7. Appeals and Recalibration

| Rule ID | Rule Name | Description |
|---|---|---|
| BR-36 | Appeal and Recalibration | An appeal may raise the manager rating for no more than two assigned goals, by at most one point per goal. `RERUN_UNIT` recalculates the affected unit or pool, and `appeal_changes.csv` records employees whose final ratings changed. |

## Week 3 Compliance Matrix

The matrix records implementation evidence and tests that assert expected
behavior, rather than only checking that a function runs. "Assumption" status
means a configurable behavior was added to complete the implementation but is
not stated or approved in the official materials.

| BR-ID | Rule | Implementation | Test evidence and edge cases | Status |
|---|---|---|---|---|
| BR-01 | Unique employee IDs | [`official_data.py`](../src/official_data.py) — `load_official_data` | [`test_business_rules.py`](../tests/test_business_rules.py) — `test_br01_duplicate_employee_ids_are_rejected` | Implemented and tested |
| BR-02 | Required employee fields and valid unit/role/date | [`official_data.py`](../src/official_data.py) — `load_official_data` | [`test_business_rules.py`](../tests/test_business_rules.py) — `test_br02_required_fields_and_official_enums_are_validated` | Implemented and tested |
| BR-03 | Grade is G1–G7 | [`official_data.py`](../src/official_data.py) — `load_official_data` | [`test_business_rules.py`](../tests/test_business_rules.py) — `test_br03_only_supported_grades_are_accepted` | Implemented and tested |
| BR-04 | Basic salary is finite and positive | [`official_data.py`](../src/official_data.py) — `load_official_data` | [`test_business_rules.py`](../tests/test_business_rules.py) — zero, negative, NaN, and infinity cases | Implemented and tested |
| BR-05 | Goal weights total 100 | [`official_data.py`](../src/official_data.py) — weight totals and status | [`test_business_rules.py`](../tests/test_business_rules.py) — `test_br05_goal_weights_must_total_100`; [`test_official_sample_edges.py`](../tests/test_official_sample_edges.py) — EC8 totals 99 and 101 | Implemented and tested |
| BR-06 | Self and manager ratings are 1–5 | [`official_data.py`](../src/official_data.py) — rating validation | [`test_business_rules.py`](../tests/test_business_rules.py) — `test_br06_self_and_manager_ratings_must_be_between_one_and_five`; blank and out-of-range values | Implemented and tested |
| BR-07 | Every required goal and competency has manager rating | [`official_data.py`](../src/official_data.py) — `load_competency_catalog`, `load_official_data` | [`test_business_rules.py`](../tests/test_business_rules.py) — missing goals/competencies, employee override, duplicate and unknown competency IDs; [`test_official_sample_edges.py`](../tests/test_official_sample_edges.py) — provisional catalog matches observed IDs | Implemented with provisional catalog assumption; faculty confirmation needed |
| BR-08 | Weighted goal score | [`scoring.py`](../src/scoring.py) — `calculate_raw_scores` | [`test_scoring.py`](../tests/test_scoring.py) — `test_goal_score` expected weighted result | Implemented and tested |
| BR-09 | Mean competency score | [`scoring.py`](../src/scoring.py) — `calculate_raw_scores` | [`test_scoring.py`](../tests/test_scoring.py) — `test_competency_score` expected mean | Implemented and tested |
| BR-10 | Raw score is 70% goal + 30% competency | [`scoring.py`](../src/scoring.py) — `calculate_raw_scores` | [`test_scoring.py`](../tests/test_scoring.py) — `test_raw_score` expected combined result | Implemented and tested |
| BR-11 | Use manager ratings for scoring | [`scoring.py`](../src/scoring.py) — `calculate_raw_scores` | [`test_scoring.py`](../tests/test_scoring.py) — goal, competency, and raw-score expected values | Implemented and tested |
| BR-12 | Retain self-ratings, exclude from raw score | [`scoring.py`](../src/scoring.py) — score calculation | [`test_scoring.py`](../tests/test_scoring.py) — `test_self_ratings_are_retained_but_do_not_change_raw_scores` | Implemented and tested; separate gap report is optional |
| BR-13 | Exclude joiners after cutoff | [`calibration.py`](../src/calibration.py) — `check_eligibility` | [`test_calibration.py`](../tests/test_calibration.py) — `test_joined_after_cutoff`; [`test_official_sample_edges.py`](../tests/test_official_sample_edges.py) — EC3 Oct 1 | Implemented and tested |
| BR-14 | Joiners on cutoff remain eligible | [`calibration.py`](../src/calibration.py) — `check_eligibility` | [`test_calibration.py`](../tests/test_calibration.py) — `test_joined_on_cutoff`; [`test_official_sample_edges.py`](../tests/test_official_sample_edges.py) — EC3 Sep 30 | Implemented and tested |
| BR-15 | Prorate mid-cycle joiners | [`compensation.py`](../src/compensation.py) — `calculate_proration` | [`test_compensation.py`](../tests/test_compensation.py) — proration tests; [`test_official_sample_edges.py`](../tests/test_official_sample_edges.py) — EMP-0156 and cutoff joiner | Implemented and tested |
| BR-16 | Distribute within units/pools | [`calibration.py`](../src/calibration.py) — `distribute_ratings` | [`test_distribution.py`](../tests/test_distribution.py) — 20-person distribution; official EC1 | Implemented and tested |
| BR-17 | Top 10% receive rating 5 | [`calibration.py`](../src/calibration.py) — bucket sizing and assignment | [`test_distribution.py`](../tests/test_distribution.py) — 20-person distribution and boundary cases | Implemented and tested |
| BR-18 | Next 20% receive rating 4 | [`calibration.py`](../src/calibration.py) — bucket sizing and assignment | [`test_distribution.py`](../tests/test_distribution.py) — `test_rating_distribution_for_20_employees` | Implemented and tested |
| BR-19 | Next 50% receive rating 3 | [`calibration.py`](../src/calibration.py) — bucket sizing and assignment | [`test_distribution.py`](../tests/test_distribution.py) — rating counts and remainder cases | Implemented and tested |
| BR-20 | Next 15% receive rating 2 | [`calibration.py`](../src/calibration.py) — bucket sizing and assignment | [`test_distribution.py`](../tests/test_distribution.py) — `test_rating_distribution_for_20_employees` | Implemented and tested |
| BR-21 | Bottom 5% receive rating 1 | [`calibration.py`](../src/calibration.py) — bucket sizing and assignment | [`test_distribution.py`](../tests/test_distribution.py) — `test_rating_distribution_for_20_employees` | Implemented and tested |
| BR-22 | Pool small units alphabetically | [`calibration.py`](../src/calibration.py) — `build_distribution_pools` | [`test_distribution.py`](../tests/test_distribution.py) — 9-forward-to-next, exactly 10 separate, residual sizes 1/5/9 | Implemented and tested; final-residual behavior is an assumption |
| BR-23 | Floor buckets; remainder to rating 3 | [`calibration.py`](../src/calibration.py) — `distribute_ratings` | [`test_distribution.py`](../tests/test_distribution.py) — `test_fractional_bucket_remainders_are_added_to_rating_three` | Implemented and tested |
| BR-24 | Score, goal, tenure, employee-ID tie-breaks | [`calibration.py`](../src/calibration.py) — rank sort | [`test_distribution.py`](../tests/test_distribution.py) — `test_ranking_tie_breakers`, `test_identical_scores_and_tenure_use_lower_employee_id`; EC2 | Implemented and tested |
| BR-25 | Exclude ineligible employees from distribution | [`calibration.py`](../src/calibration.py) — pool and result generation | [`test_distribution.py`](../tests/test_distribution.py) — `test_ineligible_employees_receive_no_distribution_rating`; EC3 | Implemented and tested |
| BR-26 | Rating-to-increment rates | [`compensation.py`](../src/compensation.py) — `INCREMENT_RATES`, `calculate_compensation` | [`test_compensation.py`](../tests/test_compensation.py) — `test_br26_increment_rates_for_every_final_rating` | Implemented and tested |
| BR-27 | Add increment to current basic | [`compensation.py`](../src/compensation.py) — `calculate_compensation` | [`test_compensation.py`](../tests/test_compensation.py) — rating increment expected values; EC4 | Implemented and tested |
| BR-28 | Round revised salary up to Rs 100 | [`compensation.py`](../src/compensation.py) — `calculate_compensation` | [`test_compensation.py`](../tests/test_compensation.py) — `test_salary_rounding` | Implemented and tested |
| BR-29 | Rs 25,000 minimum for rating 3+ | [`compensation.py`](../src/compensation.py) — compensation and annual budget cost | [`test_compensation.py`](../tests/test_compensation.py) — minimum-floor tests; official EC7 | Implemented and tested |
| BR-30 | No increment for ineligible employees | [`calibration.py`](../src/calibration.py), [`workflow.py`](../src/workflow.py) — ineligible result handling | [`test_compensation.py`](../tests/test_compensation.py) — `test_zero_proration_after_cutoff`; [`test_official_sample_edges.py`](../tests/test_official_sample_edges.py) — EC3 | Implemented and tested |
| BR-31 | Rating-5 promotion after 24 months | [`promotion.py`](../src/promotion.py) — `check_promotion_eligibility` | [`test_promotion.py`](src/tests/test_promotion.py) — rating-5 eligibility and exact 24-month boundary | Implemented and tested |
| BR-32 | Rating-4 promotion after 36 months | [`promotion.py`](../src/promotion.py) — `check_promotion_eligibility` | [`test_promotion.py`](src/tests/test_promotion.py) — rating-4 eligibility and exact 36-month boundary | Implemented and tested |
| BR-33 | Additional 5% for promotion | [`compensation.py`](../src/compensation.py) — promotion rate and scaling | [`test_compensation.py`](../tests/test_compensation.py) — selected promotion, no double count, target-grade cap | Implemented and tested |
| BR-34 | Per-unit promotion cap is ceil(8%) | [`promotion.py`](../src/promotion.py) — `select_promotions` | [`test_promotion.py`](src/tests/test_promotion.py) — `test_promotion_limit_uses_ceiling_and_selects_highest_raw_scores`; EC5 | Implemented and tested |
| BR-35 | Select candidates by raw score | [`promotion.py`](../src/promotion.py) — candidate ordering | [`test_promotion.py`](src/tests/test_promotion.py) — cap selection and score order; EC5 | Implemented and tested |
| BR-36 | Appeal changes at most two goals by at most one; rerun and report changes | [`appeals.py`](../src/appeals.py), [`workflow.py`](../src/workflow.py) — `_appeal`, `_rerun_unit` | [`test_appeals.py`](../tests/test_appeals.py) — recalibration/report and >2 rejection; [`test_official_workflow.py`](../tests/test_official_workflow.py) — >1 rejection and exact report schema; EC6 | Implemented and tested |

## Assumptions and outstanding faculty confirmation

| Area | Configured implementation | Status |
|---|---|---|
| BR-07 competency catalog | [`competency_catalog.json`](../data/input/competency_catalog.json) is marked `PROVISIONAL`; its four IDs were observed in the supplied ratings file, with a default required list and employee-specific overrides supported. Observed rows are not treated as proof of completeness. | Need faculty-confirmed catalog or per-employee required IDs |
| Promotion grade and tenure | Use grade-band file order for the next grade; do not promote the highest grade; set selected employees' `months_in_grade` to zero. The promotion increment is counted once. | Explicit implementation assumption; not faculty-approved |
| Final small pool | Distribute a final pool below 10 with ordinary bucket sizes and the remainder-to-rating-3 rule. | Explicit fallback assumption; not faculty-approved |
| Rating-gap report | No separate report is generated; self-ratings are retained and excluded from raw score. | Not a mandatory output; separate schema/formula would be needed if requested |

The official sample pack does not provide expected output files. EC1–EC8 and
the documented additional cases are tested against the actual supplied data;
synthetic tests cover boundaries not exercised by that sample, including
grade-cap lump sums. No assumption above is represented as faculty-approved.
