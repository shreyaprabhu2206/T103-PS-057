# PS-057 Decision Log

This log records confirmed rules, configuration decisions, and implementation assumptions used in the PS-057 project. Current values and behaviours are preserved as documented.

## 1. Original Brief Rule-Number Cross-Reference

| Internal BR-ID | Original Capstone Rule | Cross-reference and scope |
|---|---|---|
| BR-07 — Missing Rating Validation | Rule 1 (related, not a direct equivalence) | Rule 1 states that manager ratings are used for raw scoring and defines the score inputs and weights. BR-07 adds a completeness check requiring manager ratings for every configured required goal and competency before scoring. The competency catalog and employee-specific competency requirements are managed through the project configuration. |
| BR-22 — Small Business Unit Pooling | Rule 3 | Rule 3 requires units with fewer than 10 eligible employees to be pooled with the next unit alphabetically before distribution. The implementation also defines the treatment of a final pool that remains below 10 employees. |

**Original Rule 7** concerns promotion eligibility, the additional 5% increment, and the months-in-grade reset. It is separate from BR-07 and BR-22. The reset is recorded as confirmed in DL-01.

## 2. Decision Register

| ID | Topic | Current decision / implementation | Reason / source | Status |
|---|---|---|---|---|
| DL-01 | Months-in-grade after promotion | Set `months_in_grade` to `0` after every successful promotion; non-promoted employees retain their existing value. | Original Capstone Rule 7 and Capstone clarification; applied in `src/workflow.py` and `main.py`; covered by the promotion tests. | **CONFIRMED** |
| DL-02 | Grade-band minimum and maximum values | Preserve and load the supplied values from `data/input/grade_bands.csv` without replacement. The current maximum is used as the salary cap. | The supplied CSV is the source of the current sample values. | **CURRENT CONFIGURATION** |
| DL-03 | Promotion grade progression | Advance to the next grade in the loaded `grade_bands.csv` order and exclude the last grade from promotion. | Implemented in `src/promotion.py` through `next_grade_in_order` and `select_promotions`. | **CURRENT IMPLEMENTATION** |
| DL-04 | Company multiplier | Keep the sample value `1.05`. | Supplied through `SET_COMPANY_MULTIPLIER` in root `commands.txt` and `data/input/commands.csv`. | **SAMPLE-RUN CONFIGURATION** |
| DL-05 | Competency catalog and default requirements | `src/official_data.py` loads the explicit catalog, uses `default_required_competencies` for employees without an override, and marks an employee `INVALID_RATING` if a required competency rating is missing or invalid. The current `data/input/competency_catalog.json` contains four competency IDs observed in the supplied ratings file, all required by default. | Original Rule 1 establishes manager ratings as scoring inputs. The catalog provides the configured validation requirements. | **CURRENT CONFIGURATION** |
| DL-06 | Employee-specific competency requirements | `src/official_data.py` supports `employee_required_competencies` overrides. When an employee has no override, the default required list applies. The current mapping in `data/input/competency_catalog.json` is empty. | The configuration supports employee-specific requirements without inventing requirements for individual employees. | **IMPLEMENTED CONFIGURATION** |
| DL-07 | Final alphabetical pool below 10 eligible employees | `src/calibration.py` groups eligible units alphabetically, adding subsequent units until the pool has at least 10 employees or no units remain. A final pool below 10 is retained as a residual pool: normal rating bucket sizes are floored and the remainder is assigned to rating 3. | Implements the alphabetical pooling requirement in Original Rule 3 and defines the final residual-pool behaviour. | **DOCUMENTED IMPLEMENTATION ASSUMPTION** |

## 3. Capstone Team Clarification Record

The Capstone team acknowledged the five clarification points and instructed Team T103 to continue using the existing implementation choices while the points are checked against the supplied sample data pack.

The clarification points cover:

1. Grade-band minimum and maximum values.
2. Promotion grade progression.
3. Company multiplier.
4. Competency catalog and default requirements.
5. Final alphabetical pool below 10 employees.

The team indicated that these points would be addressed through the original assignment email thread, **“Capstone Project Assignment – Team T103 – PS-057.”**

The current implementation retains the documented values and behaviours. No replacement values or additional policy decisions have been introduced.

## 4. Reporting Scope — Self-Rating Gap Report

Original Capstone Rule 1 states that self-ratings are used only for the gap report.

The implementation retains self-ratings and excludes them from raw-score calculation. The current report contract defines:

- `letters.csv`
- `distribution.csv`
- `appeal_changes.csv`

A separate rating-gap report is not included in the current CSV output set. Its fields and calculation method are not defined in the supplied report contract.

The current implementation's reporting scope is therefore limited to the three specified CSV reports.

## 5. Decision-Log Maintenance

- Preserve the existing configuration values and implementation behaviours.
- Do not replace sample data values or invent missing policy requirements.
- Record new decisions with their original Capstone rule references.
- Update implementation and relevant tests when an authoritative clarification changes a design decision.
- Keep reporting-scope details separate from the five configuration points.
- Retain this log as the record of design decisions, implementation assumptions, and confirmation status.