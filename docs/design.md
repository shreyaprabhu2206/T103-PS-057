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