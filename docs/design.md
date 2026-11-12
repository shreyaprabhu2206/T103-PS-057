# T103-PS-057 Design Document

## 1. Project Overview
A command-line employee performance appraisal system.

## 2. Technology
- Python 3.10+
- CSV input and output
- Python unittest for automated testing

## 3. Main Modules
- Models
- Validation
- Raw Scoring
- Bell-Curve Calibration
- Compensation
- Appeals
- Reports

## 4. Business Rules
BR-01: Goal weights must sum to 100 per employee.
BR-02: Goal scores contribute 70% of the raw score.
BR-03: Competency scores contribute 30% of the raw score.
BR-04: Manager ratings determine performance scores.
BR-05: Self-ratings are used for the rating-gap report.

## Variable pay

The command file configures the company multiplier as
`SET_COMPANY_MULTIPLIER|1.05`. The configured value must be between 0.8 and
1.2. Variable pay uses the employee's current monthly basic salary multiplied
by 12, the target rate for the grade group, the final-rating multiplier, and
the company multiplier. PIP employees receive zero variable pay. The payout
is rounded to the nearest rupee, with half rupees rounded up.

## Promotion implementation note

Promotion eligibility, the per-business-unit 8% ceiling, highest-raw-score
selection, and the additional 5% increment are implemented. The assignment
does not specify a promoted-grade mapping, so promotion does not change an
employee's grade or grade-start date yet. The promoted grade's salary band and
tenure reset remain pending confirmation of the official mapping.

## Official command workflow, compensation, and reports

The official sample pack is driven by root-level `commands.txt`, processed
strictly in file order. `LOAD|employees.csv|goals.csv|ratings.csv|grade_bands.csv|units.csv`
resolves data files beside the command file or under its `data/input/`
directory. `SET_COMPANY_MULTIPLIER` is read only from the command file; unit
budgets are not used to derive this multiplier.

The official appeal syntax is
`APPEAL|appeal_id|emp_id|goal_id|new_rating[|goal_id|new_rating]`. An eligible
employee may change at most two assigned goals, and each manager rating may
increase by no more than one point. `RERUN_UNIT|unit` recalibrates that unit or
its existing distribution pool. Rejected appeals do not modify ratings.

`grade_bands.csv` supplies both bounds for all seven grades. Revised basic is
capped at the current grade's `band_max`; excess is recorded as a one-time
lump sum. The grade minimum is loaded and validated, but no salary-floor rule
based on `band_min` is specified. The official command workflow does not map
selected promotions to a new grade or reset grade tenure; the selected
employee receives the promotion increment and their current grade remains
unchanged until an official mapping is supplied.

`units.csv` supplies annual increment-cost budgets. Scaling uses annualized
cost after proration, salary rounding, the Rs 25,000 minimum floor, and grade
caps; scaled percentage rates are floored to one decimal percentage point.
PIP employees receive no increment or variable pay.

Proration follows the sample-pack scenarios: the June 15 joiner receives
three completed months, while a September 30 cutoff-day joiner receives the
documented April–September six-month proration. A joiner after the cutoff is
not eligible.

`PRINT_DISTRIBUTION|ALL` appends one row for each pool and rating at each
print command. `PRINT_LETTERS|ALL` writes one row per employee after the latest
rerun. `appeal_changes.csv` records employees whose final rating changed on a
rerun. All three report column names and order follow the official sample-pack
README. Distribution `emp_ids` are comma-separated in rank order.

The report columns, in order, are:

- `letters.csv`: `emp_id, unit, eligible, raw_score, goal_score,
  final_rating, increment_pct, pro_rated, revised_basic, lump_sum,
  variable_payout, promoted, new_grade, pip, status_code`
- `distribution.csv`: `print_no, unit_or_pool, eligible_count, rating,
  bucket_size, emp_ids`
- `appeal_changes.csv`: `appeal_id, unit_or_pool, emp_id, rating_before,
  rating_after`

For letters, `status_code` is `OK`, `NOT_ELIGIBLE`, `INVALID_WEIGHTS`, or
`INVALID_RATING`. `new_grade` is left blank because no promoted-grade mapping
is present in the official materials.

Promotion eligibility uses the supplied `months_in_grade`, the documented
rating thresholds, and the per-unit 8% cap rounded up. The promotion-grade
mapping remains unresolved because the official materials do not define one.