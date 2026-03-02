from pydantic import BaseModel
from typing import List, Optional

class SubmissionCreate(BaseModel):
    user_email: str
    section_name: str
    tasks_completed: List[str]
    notes: Optional[str] = None
    sales_amount: float

class DailySummary(BaseModel):
    total_sales: float
    submission_count: int
    missing_sections: List[str]