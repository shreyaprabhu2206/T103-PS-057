from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Employee:
    employee_id: str
    business_unit: str
    grade: str
    basic_salary: int
    joining_date: date
    manager_id: str
    current_role_band: str
    grade_start_date: date
    previous_final_rating: Optional[int] = None


@dataclass
class Goal:
    employee_id: str
    goal_id: str
    goal_name: str
    weight: int


@dataclass
class Rating:
    employee_id: str
    item_type: str
    item_id: str
    self_rating: int
    manager_rating: int