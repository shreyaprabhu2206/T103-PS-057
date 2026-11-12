# T103-PS-057 Design Document

## 1. Overview

PS-057 is a Python command-line appraisal engine. It loads employee, goal,
rating, grade-band, unit-budget, and competency-catalog data; computes scores
and normalized ratings; applies appeals and reruns; calculates compensation;
and writes the required CSV reports.

## 2. Modules

| Module | Responsibility |
|---|---|
| `main.py` | Legacy command workflow |
| `src/official_data.py` | CSV/config loading, schema checks, employee validation statuses, competency completeness |
| `src/scoring.py` | Goal, competency, and combined raw scores |
| `src/calibration.py` | Eligibility, alphabetical pooling, ranking, and bell-curve assignment |
| `src/promotion.py` | Promotion eligibility, unit cap, selection, and grade-order helper |
| `src/compensation.py` | Increment rates, budget scaling, salary cap/lump sum, proration, PIP, variable pay |
| `src/appeals.py` | Validate rating changes and recalculate scores |
| `src/workflow.py` | Process official commands in order; coordinate reruns and report output |
| `src/reports.py` | Required report schemas and CSV serialization |
| `tests/` and `docs/src/tests/` | Business-rule, edge, integration, and promotion tests |

## 3. Official command processing

The root `commands.txt` is read sequentially. `SET_APPRAISAL_YEAR` and
`SET_COMPANY_MULTIPLIER` configure the run before `LOAD`. `LOAD` accepts the
five official CSV paths and an optional sixth competency-catalog path. When
omitted, the workflow looks for `competency_catalog.json` beside
`ratings.csv`.

`RUN_APPRAISAL` loads validated data, excludes employees with invalid
weights/ratings from scoring, computes scores and distribution, selects
eligible promotions, then calculates compensation. `APPEAL` validates a
change to one or two assigned goals, rejecting changes above one point.
`RERUN_UNIT` identifies the current distribution pool containing the named
unit, recalculates that pool and records final-rating changes. Distribution
prints append a snapshot in command order; letters reflect the latest
completed run. At the end of the workflow, promoted employee objects have
their assumed next grade and `months_in_grade = 0`.

## 4. Data validation and scoring

The loader checks employee uniqueness and required fields, valid grades,
salary, goal weights, rating ranges, required goal ratings, competency IDs,
duplicates, and required competency rows. Competency completeness is governed
by the JSON configuration; the loader does not infer a complete catalog from
observed rating rows.

Goal score is the weighted mean of manager goal ratings; competency score is
the mean of manager competency ratings; raw score is 70% goal score plus 30%
competency score. Self-ratings are retained and do not contribute to raw
score.

## 5. Calibration and final residual pool

Eligible units with fewer than 10 employees are pooled forward in alphabetical
order until the pool reaches 10 or no units remain. **Implementation
assumption:** a final residual pool below 10 is still distributed using the
ordinary bucket calculation: floor each percentage bucket and assign the
unallocated remainder to rating 3. This fallback is explicitly an
implementation assumption and has not been approved by faculty.

Ranking uses raw score, goal score, joining date (longer service first), and
employee ID. Employees outside eligibility do not enter a distribution.

## 6. Promotion and compensation

Official promotion eligibility is rating 5 with at least 24 months in grade,
or rating 4 with at least 36 months. The limit is the ceiling of 8% of each
eligible unit headcount, and candidates are chosen by raw score. The
additional 5% is included once in the scaled total increment rate; the
promotion increment is not added a second time during compensation.

**Implementation assumptions, not official rules:** grade progression follows
the row order in `grade_bands.csv`; employees at its last grade are excluded
from promotion; `months_in_grade` resets to zero for a selected promotion.
The grade-band cap used for compensation is the target grade's `band_max`.
Revised basic is capped there, and any excess is recorded as a one-time lump
sum. These assumptions require faculty confirmation and are not represented
as faculty-approved rules.

Unit budgets are annual costs. Budget scaling evaluates the resulting annual
increment cost after proration, salary rounding, the Rs 25,000 minimum floor,
and grade caps. The official command sets the company multiplier; it is not
derived from unit budgets.

PIP employees receive no increment or variable pay. Variable pay uses the
current basic salary, target percentage for grade, final-rating multiplier,
and configured company multiplier.

## 7. Reports

The mandatory output reports and column orders are:

- `letters.csv`: `emp_id, unit, eligible, raw_score, goal_score,
  final_rating, increment_pct, pro_rated, revised_basic, lump_sum,
  variable_payout, promoted, new_grade, pip, status_code`
- `distribution.csv`: `print_no, unit_or_pool, eligible_count, rating,
  bucket_size, emp_ids`
- `appeal_changes.csv`: `appeal_id, unit_or_pool, emp_id, rating_before,
  rating_after`

Distribution rows follow `PRINT_DISTRIBUTION` execution order. Letters contain
one row per employee, sorted by ID. Appeal changes contain employees whose
final rating changed after recalibration. A separate rating-gap report is
optional and is not generated; it is not in the mandatory output contract.

## 8. Verification and unresolved external information

Run `python -B -m unittest discover -v` from the project root and execute the
official workflow with `python -B main.py --commands commands.txt
--output-dir output`. The test suite includes the actual sample data scenarios
EC1–EC8 and extra documented cases, plus synthetic boundary tests where the
sample data does not exercise a behavior such as a grade-cap lump sum.

See the [Week 3 compliance matrix](business_rules.md#week-3-compliance-matrix)
for each BR-ID's implementation and test. Faculty confirmation is still
needed for the competency catalog, promotion-grade/tenure policy, and
final-residual-pool policy. No expected output files are supplied by the
official sample pack. A gap report remains optional; if requested, its
formula and schema would need to be specified separately.
