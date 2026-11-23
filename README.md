# PS-057 – Performance Appraisal and Bell-Curve Normalisation with Increment Bands

A command-file-driven Python backend that automates employee performance appraisal, forced-distribution calibration, compensation calculations, appeals, and CSV reporting.

**Project:** T103 – PS-057  
**Team:** T103, Section ISE D  
**Status:** Implementation and testing completed

## Overview

PS-057 implements an appraisal workflow for employee data, combining manager-assigned goal and competency ratings, applying eligibility and unit-level bell-curve normalisation, and calculating increments, promotions, and variable pay within budget constraints.

The application is designed as a backend command-line engine. It has no user interface and uses CSV/JSON files for inputs and outputs.

## Features

- Input validation for employee, goal, rating, grade-band, competency, and budget data.
- Weighted goal-score and competency-score calculations.
- Raw score calculation using 70% goal score and 30% competency score.
- Eligibility checks and completed-month prorating for eligible joiners.
- Small-unit pooling and forced rating distribution.
- Deterministic tie-breaking.
- Appeal processing and unit/pool recalibration.
- Promotion eligibility, unit promotion limits, and grade progression.
- Increment calculation, salary rounding, grade-band caps, and lump-sum handling.
- Budget scaling and minimum revised-basic salary floor.
- PIP identification and compensation exclusions.
- Variable-pay calculation.
- CSV report generation.

## Technology Stack

- Python 3.10+
- Python standard library
- CSV and JSON
- `unittest`

No third-party runtime packages are required.

## Project Structure

```text
T103-PS-057/
├── main.py
├── src/
│   ├── models.py
│   ├── validation.py
│   ├── scoring.py
│   ├── calibration.py
│   ├── compensation.py
│   ├── promotion.py
│   ├── appeals.py
│   ├── official_data.py
│   ├── reports.py
│   └── workflow.py
├── tests/
├── docs/
│   ├── business_rules.md
│   ├── design.md
│   ├── decision_log.md
│   ├── glossary.md
│   ├── class_diagram.md
│   └── state_diagram.md
├── data/
│   └── input/
├── official_sample_data_pack/
├── output/
├── commands.txt
├── COMMANDS.md
├── requirements.txt
└── README.md
```

## Business Rules Implemented

- Goal scores use manager ratings and employee goal weights.
- Competency scores use manager ratings.
- Raw score = 70% goal score + 30% competency score.
- Self-ratings are retained but do not contribute to the raw score.
- Employees joining after the appraisal cutoff are excluded; eligible mid-year joiners receive prorated increments.
- Unit distribution follows the prescribed 10%, 20%, 50%, 15%, and 5% rating buckets, with floor bucket counts and the remainder assigned to rating 3.
- Small units are pooled according to the implemented pooling logic.
- Tie-breaking uses raw score, goal score, tenure, and employee ID.
- Rating-based increments, promotions, salary rounding, grade caps, lump sums, budget scaling, and the minimum salary floor are processed by the compensation workflow.
- Promotion eligibility and unit promotion limits are applied.
- Successful promotions reset months-in-grade to zero.
- PIP employees receive no increment or variable pay.
- Valid appeals are followed by a unit or pool rerun.

## Reports

The application generates the following CSV reports in the output directory:

| Report | Description |
|---|---|
| `letters.csv` | Employee appraisal outcomes, compensation, promotion, PIP, and status details |
| `distribution.csv` | Rating bucket counts and employee membership by unit or pool for each distribution print |
| `appeal_changes.csv` | Employee final-rating changes resulting from appeals |

## Setup and Execution

### Requirements

- Python 3.10 or later
- Git

### Windows PowerShell

Run these commands from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -B main.py --commands commands.txt --output-dir output
```

### macOS/Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -B main.py --commands commands.txt --output-dir output
```

## Command File Workflow

Commands are read sequentially from `commands.txt`. Blank lines and comment lines are ignored.

| Command | Purpose |
|---|---|
| `SET_APPRAISAL_YEAR` | Configure the appraisal year and cutoff date |
| `SET_COMPANY_MULTIPLIER` | Configure the company multiplier |
| `LOAD` | Load the employee, goal, rating, grade-band, unit, and optional competency data |
| `RUN_APPRAISAL` | Run scoring, distribution, and compensation workflow |
| `APPEAL` | Submit a permitted goal-rating appeal |
| `RERUN_UNIT` | Recalibrate an affected unit or pool after an appeal |
| `PRINT_DISTRIBUTION` | Generate distribution output |
| `PRINT_LETTERS` | Generate employee outcome output |

Accepted appeals must be followed by the appropriate `RERUN_UNIT` command before another appeal or appraisal run.

## Testing

Run the test suite using:

```bash
python -B -m unittest discover -v
```

The test suite covers business-rule implementation, validation, scoring, calibration, compensation, promotions, appeals, workflow behavior, and edge cases from the supplied sample pack.

The implementation has test evidence for BR-01 through BR-37. The documented compliance matrix records 34 PASS and 3 PARTIAL, reflecting areas where the implemented behavior is tested but policy details or report scope are not fully authoritative.

## Verification and Configuration Notes

- The competency catalog used by the sample implementation is based on IDs present in the sample ratings data and is configurable.
- Grade progression follows the configured grade-band file order.
- The residual-pool fallback for a final pool smaller than ten is handled by the documented implementation.
- The company multiplier and grade-band values are configurable inputs.
- Self-rating gap-report output is not part of the current three-report output contract.

These configuration details and assumptions are documented in `docs/decision_log.md` and `docs/design.md`.

## Documentation

- `docs/business_rules.md` – business-rule definitions and compliance matrix.
- `docs/design.md` – architecture and implementation design.
- `docs/decision_log.md` – configuration decisions and implementation assumptions.
- `docs/glossary.md` – project terminology.
- `docs/class_diagram.md` – class structure.
- `docs/state_diagram.md` – workflow states.

## Project Completion

The PS-057 backend implementation, command-driven workflow, report generation, documentation, and automated test suite have been completed. The project is organized for reproducible execution and verification using the supplied sample data and documented rules.

## Project Demo

[Watch the PS-057 Project Demo](https://drive.google.com/file/d/168L7xpKtPPR9g0NJTTVcfUjiQVKOP7nH/view?usp=drivesdk)
