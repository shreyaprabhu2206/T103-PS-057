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
| BR-36 |