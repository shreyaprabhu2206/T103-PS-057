# T103-PS-057 Design Document

## 1. Overview

PS-057 is a Python command-line appraisal engine. It loads employee, goal,
rating, grade-band, unit-budget, and competency-catalog data; computes scores
and normalized ratings; applies appeals and reruns; calculates compensation;
and writes the required CSV reports.

## 2. Modules

| Module | Responsibility |
|---|---|
| `main.py` | Entry point for the ordered command workflow, with a legacy CSV path when no command file is available |
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
completed run. A valid appeal updates manager ratings but keeps the last
completed results as the pre-appeal comparison baseline and marks the
appealed employee's unit as pending a rerun. While a rerun is pending,
`RUN_APPRAISAL` is rejected with a message requiring `RERUN_UNIT` for that
unit; the pending state and baseline are retained. The pending appeal is
cleared only after the rerun and compensation refresh succeed, and
`appeal_changes.csv` records every changed final rating against the preserved
baseline. At the end of a successful workflow, promoted employee objects have
the current assumed next grade and `months_in_grade = 0`; employees who were
not promoted retain their existing months-in-grade value. The reset is an
officially confirmed rule.

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

**Working assumption awaiting confirmation:** grade progression follows the
row order in `grade_bands.csv`; employees at its last grade are excluded from
promotion. The official clarification confirms that a successful promotion
sets `months_in_grade` to zero; this is not an assumption. Employees not
promoted retain their value.

The existing grade-band values are loaded from `data/input/grade_bands.csv`
without alteration. Their minimum and maximum values are awaiting Capstone
confirmation. The implementation uses the target grade's `band_max` to cap
revised basic and records excess as a one-time lump sum; this does not confirm
that the supplied band values are official.

Unit budgets are annual costs. Budget scaling evaluates the resulting annual
increment cost after proration, salary rounding, the Rs 25,000 minimum floor,
and grade caps. The root sample `commands.txt` currently sets the company
multiplier to `1.05`; the intended multiplier is awaiting Capstone
confirmation. It is not derived from unit budgets.

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
final rating changed after recalibration. No separate rating-gap report is
generated. Original Rule 1 references self-ratings only for a gap report, but
the current output contract does not specify that report's schema or formula;
whether it is required remains an open scope question.

## 8. Verification and unresolved external information

Run `python -B -m unittest discover -v` from the project root and execute the
official workflow with `python -B main.py --commands commands.txt
--output-dir output`. The test suite includes the actual sample data scenarios
EC1–EC8 and extra documented cases, plus synthetic boundary tests where the
sample data does not exercise a behavior such as a grade-cap lump sum.

See the [Week 3 compliance matrix](business_rules.md#week-3-compliance-matrix)
for each BR-ID's implementation and test, and the [decision
log](decision_log.md) for confirmation status. Capstone confirmation is still
needed for grade-band minimum/maximum values, promotion grade progression, and
the intended company multiplier. Capstone team confirmation is also needed
for the competency catalog and final-residual-pool policy. No expected output
files are supplied by the official sample pack. The rating-gap report scope also
needs clarification before claiming that aspect of original Rule 1 is
complete.
