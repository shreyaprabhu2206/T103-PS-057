# PS-057 – Performance Appraisal and Bell-Curve Normalisation with Increment Bands — Sample Data Pack

Prepared by 10 SECONDS for Team T103.

Domain: Enterprise / HR – Performance. Build the back-end engine a 500-person company's HR team uses to collect goal and competency ratings, normalise manager scores into a forced distribution per business unit, assign final ratings and compute increments, promotions and variable pay. Command-file driven; no UI.

## Files

| File | What it holds | Rows |
|---|---|---|
| `employees.csv` | Employees (180) | 180 |
| `goals.csv` | Five goals per employee with weights | 900 |
| `ratings.csv` | Self and manager ratings per goal and competency | 1621 |
| `grade_bands.csv` | Monthly basic band per grade | 7 |
| `units.csv` | Annual increment-cost budget per unit | 6 |
| `competency_catalog.json` | Provisional competency IDs and required lists | 4 IDs |
| `commands.txt` | Command file; process strictly in file order. | 17 |

## Developer setup and usage

### Requirements

- Python 3.10 or later
- Git
- No third-party Python packages are required.

Run the following commands from the project root. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -B main.py --commands commands.txt --output-dir output
python -B -m unittest discover -v
```

On macOS or Linux, activate the virtual environment with
`source .venv/bin/activate` instead of the PowerShell activation command.
The command file loads the official CSV files from `data/input/`. If `LOAD`
does not name a competency catalog, the workflow looks for
`competency_catalog.json` beside `ratings.csv`. The application writes
`letters.csv`, `distribution.csv`, and `appeal_changes.csv` to `output/`.

The supplied competency catalog is explicitly **provisional**: it lists the
four IDs observed in `ratings.csv`, which does not prove that the catalog is
complete. It supports a default required list and employee-specific
overrides. A faculty-confirmed catalog is still needed before treating those
requirements as authoritative.

The official materials do not specify promotion grade progression or tenure
reset behavior. For this implementation only, the configurable assumption is
that a selected promotion advances to the next grade in `grade_bands.csv`
row order, excludes employees already at the last grade, and resets
`months_in_grade` to zero. This assumption is not faculty-approved. The
additional 5% promotion increment is included once in budget scaling and
compensation.

If alphabetical pooling reaches the last unit and the combined pool still
contains fewer than 10 eligible employees, the implementation processes it
as a residual pool using the normal floor bucket sizes and puts the remainder
in rating 3. This is a fallback assumption, not an official rule.

Row counts exclude the header line (CSV) and comment lines (commands.txt).

## Column reference

Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals with at most 2 decimals (no commas, no symbol); percentages as plain numbers (12.5 = 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix.

### `employees.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `emp_id` | string | EMP-nnnn |  | Primary key; final tie-break |
| `name` | string |  |  |  |
| `unit` | enum |  | ENGINEERING/FINANCE/HR/LEGAL/OPERATIONS/SALES | Distribution unit |
| `grade` | enum |  | G1–G7 |  |
| `basic_salary` | decimal | Rs per month |  | Current monthly basic |
| `date_of_joining` | date |  |  | Eligibility and pro-ration; tenure tie-break |
| `manager_id` | string |  |  | Informational |
| `months_in_grade` | integer | months |  | Promotion eligibility |
| `previous_year_rating` | integer |  | 1–5 | Consecutive rating-2 PIP rule |
| `role_band` | enum |  | IC/LEAD/MANAGER | Informational |

### `goals.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `emp_id` | string |  | employees.csv | FK |
| `goal_id` | string | EMP-nnnn-Gn |  | Primary key |
| `goal_title` | string |  |  |  |
| `weight` | integer | percent |  | Must sum to 100 per employee (two planted exceptions) |

### `ratings.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `emp_id` | string |  | employees.csv | FK |
| `item_type` | enum |  | GOAL/COMPETENCY |  |
| `item_id` | string |  | goal_id or competency code |  |
| `self_rating` | integer |  | 1–5 | Retained; not used in raw score |
| `manager_rating` | integer |  | 1–5 (one 6 and one blank planted) | Used for the raw score |

### `grade_bands.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `grade` | enum |  | G1–G7 |  |
| `band_min` | decimal | Rs per month |  |  |
| `band_max` | decimal | Rs per month |  | Revised basic cap; excess paid as lump sum |

### `units.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `unit` | enum |  |  |  |
| `increment_budget_annual` | decimal | Rs per year |  | Total cost guard: sum of (revised - current basic) x 12 |
| `unit_head` | string |  |  |  |

### General notes

- Where the brief is silent: variable pay = target% x annual basic (12 x current basic) x rating multiplier x company multiplier; pooled units are reported under the pool name 'HR+LEGAL'; percentages scaled by budget are floored to 1 decimal.
- A separate rating-gap report is not one of the three required outputs and
  is not generated. No gap formula or additional report schema is assumed.

## Command file format

`commands.txt` holds one command per line in the form `COMMAND_NAME|arg1|arg2|...`. Commands MUST be processed strictly in file order. Lines starting with `#` are comments and blank lines are ignored. Every command used in this pack, with its argument order:

| Command | Arguments (in order) | Meaning |
|---|---|---|
| `SET_APPRAISAL_YEAR` | `year|cutoff_date` | Eligibility cut-off (joiners after it are NOT_ELIGIBLE; 1 Apr–cut-off pro-rated) |
| `SET_COMPANY_MULTIPLIER` | `multiplier` | Company multiplier on variable pay |
| `LOAD` | `employees|goals|ratings|bands|units[|competency_catalog]` | Load master data and, optionally, an explicit competency catalog |
| `RUN_APPRAISAL` | `` | Compute raw scores, distribution, increments, promotions, variable pay for all units |
| `APPEAL` | `appeal_id|emp_id|goal_id|new_rating[|goal_id|new_rating]` | Raise manager rating on at most 2 goals by at most 1 point each |
| `RERUN_UNIT` | `unit` | Recompute the unit (or its pool) after an appeal and report changed ratings |
| `PRINT_DISTRIBUTION` | `ALL` | Write distribution.csv |
| `PRINT_LETTERS` | `ALL` | Write letters.csv |

## Planted scenarios

Every edge case from the brief is planted at the location given. Line numbers count the header as line 1 for CSVs and count every physical line (including comments) for commands.txt.

- **EC1: Unit with exactly 10 eligible employees (no pooling) versus 9 (pooled)** — FINANCE has 11 employees of which exactly 10 are eligible (EMP-0081 joined 2026-10-01 → NOT_ELIGIBLE) → distributed alone; HR has 10 employees of which 9 are eligible (EMP-0091 joined 2026-11-15) → pooled with LEGAL (next unit alphabetically) before distribution
- **EC2: Two employees with identical raw score, goal score and tenure** — EMP-0111 and EMP-0112 have identical goal weights, identical manager ratings (raw 3.79), identical goal-only score and the same date_of_joining 2021-06-01 → tie broken by lower employee ID
- **EC3: Joiner on exactly 30 September versus 1 October** — EMP-0080 joined exactly 2026-09-30 → eligible with pro-rated increment (completed months Apr–Sep); EMP-0081 joined 2026-10-01 → NOT_ELIGIBLE
- **EC4: Revised basic exactly at grade band max** — EMP-0011 (G3, basic 56600.00, mid-pack raw 3.43 → rating 3, 6%) → 56600 x 1.06 = 59996 rounded up to 60000.00 = G3 band_max exactly (no lump sum)
- **EC5: Promotion count where 8% of headcount is a non-integer** — SALES has 35 eligible employees → 8% = 2.8 → ceil = 3 promotions at most; EMP-0146, EMP-0147, EMP-0148, EMP-0149, EMP-0150 are all promotion-eligible, so only the top 3 by raw score are promoted
- **EC6: Appeal that changes which employee crosses the top-10% boundary** — ENGINEERING (70 eligible, top-10% = 7): EMP-0007 is 7th (raw 4.57) and EMP-0008 is 8th (raw 4.43); commands.txt line 7 APPEAL APL-01 raises EMP-0008's G1 and G2 by 1 each → raw 4.71 → it crosses into rating 5 and EMP-0007 drops to rating 4 on RERUN_UNIT
- **EC7: Budget scaling that would push a rating-3 employee below the Rs 25,000 floor** — OPERATIONS budget (units.csv) is ~55% of the unscaled cost → increment percentages scale down; EMP-0126 (G1, basic 23800.00, rating 3) would fall below 25,000 after scaling → raised to the 25,000.00 floor
- **EC8: Employee with goal weights summing to 99 or 101** — goals.csv: EMP-0094 weights sum to 99 and EMP-0095 to 101 → INVALID_WEIGHTS, excluded from the distribution
- **Extra: pro-rated mid-year joiner** — EMP-0156 joined 2026-06-15 → completed months to 30 Sep = 3 → increment x 3/12
- **Extra: PIP** — EMP-0136 has previous_year_rating 2 and bottom-band scores this year → if rated 2 again, PIP: zero increment and zero variable; EMP-0070 has the lowest ENGINEERING raw → rating 1 → PIP
- **Extra: invalid appeals** — commands.txt line 11 APL-03 raises a goal by 2 points → reject; line 13 APL-04 touches 3 goals → reject; APL-02 and APL-05 are valid single-goal +1 appeals
- **Extra: bad rating rows** — ratings.csv line 103 duplicates line 102 → use once; line 872 manager_rating 6 → invalid (treat employee as INVALID_RATING and exclude); line 876 blank manager_rating → INVALID_RATING
- **Extra: grade cap lump sum** — Several employees have basic within 5% of band_max; a 10% or 14% increment must be capped at band_max with the excess as a one-time lump sum

## Week 3 compliance summary

- **Implemented and tested:** BR-01–BR-36 have meaningful implementation and
  expected-result tests. BR-07 validation uses the explicit catalog
  configuration. See the [BR-ID compliance matrix](docs/business_rules.md#week-3-compliance-matrix).
- **Implementation assumptions, not official rules:** provisional sample-derived
  competency catalog; next-grade promotion in grade-band file order, no
  promotion from the highest grade, and tenure reset to zero; residual-pool
  fallback for a final pool smaller than 10. Tests cover each assumption.
- **Not required / not implemented:** a separate rating-gap report. The three
  required CSV schemas are unchanged.
- **Still requiring faculty confirmation:** the complete competency catalog
  and required IDs per employee, official promotion-grade and tenure-reset
  policy, and the intended behavior for a final pool below 10. The current
  assumptions do not claim faculty approval.

The official sample pack does not provide expected output files; verification
is based on stated rules, actual input data, and planted scenarios rather than
invented expected outputs.

## What is NOT in this pack

Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-nn). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation

Produce these files (CSV, header row, same conventions as above, rows in the order stated). Numeric columns must be plain decimals with exactly the decimals stated.

### `letters.csv`

One row per employee after the final RERUN, ordered by emp_id.

Columns in order: `emp_id`, `unit`, `eligible`, `raw_score`, `goal_score`, `final_rating`, `increment_pct`, `pro_rated`, `revised_basic`, `lump_sum`, `variable_payout`, `promoted`, `new_grade`, `pip`, `status_code`

### `distribution.csv`

One row per unit (or pool) per rating per PRINT_DISTRIBUTION, in command order.

Columns in order: `print_no`, `unit_or_pool`, `eligible_count`, `rating`, `bucket_size`, `emp_ids`

### `appeal_changes.csv`

Employees whose final rating changed after each appeal.

Columns in order: `appeal_id`, `unit_or_pool`, `emp_id`, `rating_before`, `rating_after`
