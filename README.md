# Performance Appraisal and Bell-Curve Normalisation with Increment Bands

## Project Information

 Field Details 

 Project ID : T103-PS-057 
 Team       : T103 
 Section    : ISE D 
 Programming Language : Python 3.10+ 
 Project Type : Command-file Based Backend 
 Domain : Human Resource Management 

## 1. Project Overview

Performance appraisal is an important process used by organisations to evaluate employee performance and determine salary increments, promotions and variable pay.

In many organisations, managing employee ratings manually can be time-consuming and inconsistent. This project aims to develop a Python-based Performance Appraisal and Bell-Curve Normalisation system that automates the appraisal process using predefined business rules.

The system processes employee information, goals, ratings and compensation budgets from CSV files. It calculates performance scores, applies bell-curve normalisation and determines compensation based on the final appraisal ratings.

## 2. Problem Statement

Organisations need a consistent way to evaluate employee performance and distribute ratings fairly across business units.

Manual appraisal processes can lead to calculation errors, inconsistent ratings and difficulties in managing compensation budgets.

This project addresses these challenges by developing an automated system that validates employee data, calculates appraisal scores, assigns final ratings and determines compensation according to defined business rules.

## 3. Project Objectives

- Automate the employee performance appraisal process.
- Validate employee, goal and rating information.
- Calculate weighted goal scores and competency scores.
- Determine raw appraisal scores.
- Apply bell-curve normalisation to assign final ratings.
- Calculate salary increments and revised basic salaries.
- Support promotion and variable-pay calculations.
- Apply compensation budget constraints.
- Generate appraisal results using a command-based workflow.

## 4. Key Features

- **CSV-based input:** Reads employee, goal, rating and budget information from CSV files.
- **Input validation:** Checks required fields, rating ranges and goal-weight totals.
- **Performance scoring:** Calculates goal, competency and raw appraisal scores.
- **Eligibility checking:** Determines employee eligibility based on appraisal rules.
- **Bell-curve normalisation:** Assigns final ratings according to the specified distribution.
- **Compensation calculation:** Calculates increments and revised salaries.
- **Budget management:** Supports business-unit compensation budget rules.
- **Automated testing:** Tests important business rules and calculations.

*Note: Advanced features are subject to completion and verification against the assignment requirements.*

## 5. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Backend development |
| CSV | Input data storage |
| Git | Version control |
| GitHub | Source code collaboration |
| VS Code | Development environment |
| unittest / pytest | Automated testing, depending on the configured test framework |


## 6. Input Files

The application uses the following CSV files:

| File | Description |
|---|---|
| employees.csv | Contains employee details such as ID, business unit, grade, salary and joining date. |
| goals.csv | Contains employee goals and their assigned weights. |
| ratings.csv | Contains self-ratings and manager ratings. |
| budgets.csv | Contains compensation budgets for business units. |
| commands.csv | Contains commands or operations for the application workflow. |

## 7. Application Workflow

The application follows these major stages:

1. Load input data from CSV files.
2. Validate employee, goal, rating and budget information.
3. Calculate weighted goal scores.
4. Calculate competency scores.
5. Calculate raw appraisal scores.
6. Check employee eligibility.
7. Apply bell-curve normalisation.
8. Assign final appraisal ratings.
9. Calculate increments and compensation.
10. Generate appraisal results.

## 8. Bell-Curve Rating Distribution

The project uses the following target rating distribution:

| Final Rating | Distribution |
|---|---:|
| 5 – Outstanding | 10% |
| 4 – Exceeds Expectations | 20% |
| 3 – Meets Expectations | 50% |
| 2 – Needs Improvement | 15% |
| 1 – Unsatisfactory | 5% |
| **Total** | **100%** |

## 9. Performance Score Calculation

The raw appraisal score is calculated using the following formula:

**Raw Score = (70% × Goal Score) + (30% × Competency Score)**

Goal scores are calculated using the assigned goal weights, while competency scores are calculated using manager ratings.


## 10. Documentation

Detailed project documentation is available in the `docs/` directory:

- `business_rules.md` – Business rules followed by the application.
- `glossary.md` – Definitions of important project terms.
- `class_diagram.md` – UML class diagram.
- `state_diagram.md` – UML state diagram.

## 11. Team Collaboration

The project uses Git and GitHub for version control and collaboration.

Team members can clone the repository, create their own branches, implement assigned modules, test their changes and push updates to GitHub.

Before starting work, team members should pull the latest changes from the shared repository.

## 12. Expected Outcome

The expected outcome is a Python-based appraisal system that processes employee performance data, applies predefined appraisal and calibration rules, and calculates compensation-related results.

The system aims to reduce manual calculations, improve consistency and make the appraisal process easier to manage.

---

**Project:** T103-PS-057  
**Team:** T103  
**Department:** Information Science and Engineering