# PS-057 Decision Log

This log distinguishes confirmed rules from provisional configuration and
working assumptions. Preserve the current values and behaviors until the
Capstone team or faculty provides an authoritative clarification.

## Original brief rule-number cross-reference

The following mappings use the original-rule excerpts supplied by the
Capstone team. They distinguish original business rules from additional
implementation-level validation and do not infer requirements absent from
those excerpts.

| Internal BR-ID | Original Capstone rule | Cross-reference and scope |
|---|---|---|
| BR-07 — Missing Rating Validation | Rule 1 (related, not a direct equivalence) | Rule 1 states that manager ratings are used for raw scoring and defines the score inputs and weights. BR-07 adds a completeness check requiring manager ratings for every configured required goal and competency before scoring. Rule 1 does not define the authoritative competency catalog or which competencies are required for each employee; those are additional implementation-level validation requirements and remain pending confirmation. |
| BR-22 — Small Business Unit Pooling | Rule 3 | Rule 3 explicitly requires units with fewer than 10 eligible employees to be pooled with the next unit alphabetically before distribution. It does not specify what to do if the final pool still has fewer than 10 because no next unit remains; that residual-pool behavior remains an unconfirmed implementation assumption. |

Original Rule 7 concerns promotion eligibility, the additional 5% increment,
and the months-in-grade reset. It is separate from BR-07 and BR-22; the reset
is recorded as confirmed in DL-01.

| ID | Topic | Current decision / assumption | Reason / source | Status |
|---|---|---|---|---|
| DL-01 | Months-in-grade after promotion | Set `months_in_grade` to `0` after every successful promotion; non-promoted employees retain their existing value. | Original Capstone Rule 7 and latest Capstone clarification; applied in `src/workflow.py` and `main.py`; covered by `test_promotions_advance_grade_reset_tenure_and_respect_new_band_cap`. | **CONFIRMED** |
| DL-02 | Grade-band minimum and maximum values | Preserve and load the supplied values from `data/input/grade_bands.csv` without replacement. The current maximum is used as the salary cap. | The existing CSV is the source of the sample values; the Capstone team is checking the official minimum and maximum values. No replacement values are supplied. Different confirmed values could change capped salary, lump sums, and budget calculations. | **WORKING ASSUMPTION — PENDING CAPSTONE CONFIRMATION** |
| DL-03 | Promotion grade progression | Preserve the current working behavior: advance to the next grade in the loaded `grade_bands.csv` order and exclude the last grade from promotion. | Current implementation: `src/promotion.py` (`next_grade_in_order`, `select_promotions`) and `src/workflow.py`. The Capstone team is checking the intended progression; a different decision could change promoted grades and related salary caps and compensation. | **WORKING ASSUMPTION — PENDING CAPSTONE CONFIRMATION** |
| DL-04 | Company multiplier | Keep the current sample value `1.05`. | It is supplied by `SET_COMPANY_MULTIPLIER` in root `commands.txt` and `data/input/commands.csv`; these are sample command inputs, not evidence of official policy. A different confirmed value would change variable-pay amounts. | **WORKING ASSUMPTION — PENDING CAPSTONE CONFIRMATION** |
| DL-05 | Authoritative competency catalog and default requirements (internal BR-07; related to original Rule 1) | `src/official_data.py` loads the explicit catalog, uses `default_required_competencies` for employees without an override, and marks an employee `INVALID_RATING` if a required competency rating is missing or invalid. The current `data/input/competency_catalog.json` is `PROVISIONAL`: its four IDs were observed in the supplied ratings file, and all four are currently required by default. These observations are not authoritative. | Original Rule 1 establishes that manager ratings contribute to scoring, but does not state the authoritative competency catalog or required competency list. Those remain additional implementation-level validation details awaiting Capstone confirmation. A different confirmed catalog/list could change which employees are marked `INVALID_RATING` and downstream appraisal results. | **WORKING ASSUMPTION — PENDING CAPSTONE CONFIRMATION** |
| DL-06 | Employee-specific competency requirements (internal BR-07; additional implementation-level requirement beyond original Rule 1) | `src/official_data.py` supports `employee_required_competencies` overrides; when an employee has no override, the default required list applies. The current mapping in `data/input/competency_catalog.json` is empty. Do not invent employee-specific requirements. | Original Rule 1 does not specify per-employee competency requirements. The authoritative mapping is awaiting Capstone confirmation; a different mapping could change which employees are marked valid or `INVALID_RATING` and affect downstream results. | **WORKING ASSUMPTION — PENDING CAPSTONE CONFIRMATION** |
| DL-07 | Final alphabetical pool below 10 eligible employees (internal BR-22; original Rule 3) | `src/calibration.py` groups eligible units in alphabetical order, adding subsequent units until the pool has at least 10 employees or no units remain. A final pool still below 10 is retained as a residual pool: normal rating bucket sizes are floored and the remainder is assigned to rating 3. | Original Rule 3 requires pooling with the next alphabetic unit before distribution, but does not specify a final pool with no next unit. The Capstone team is checking this case. A different decision could change final-pool rating allocation and affected employees' downstream results. | **WORKING ASSUMPTION — PENDING CAPSTONE CONFIRMATION** |

## Open reporting-scope issue (separate from the five pending policy clarifications)

Original Rule 1 says self-ratings are used only for the gap report. The
implementation retains self-ratings and excludes them from raw-score
calculation, but it does not generate a separate rating-gap report. The
current report contract defines `letters.csv`, `distribution.csv`, and
`appeal_changes.csv`; it does not provide a gap-report schema or formula.
Confirm whether a separate gap report is required and, if so, its fields and
calculation before claiming full Rule 1 reporting compliance. This scope issue
does not change the five pending policy clarifications recorded above.
