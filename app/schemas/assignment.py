from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    user_id: int
    asset_ids: List[int]


class AssignmentResponse(BaseModel):
    id: int
    user_id: int
    assignment_date: datetime
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationCreate(BaseModel):
    assignment_id: int
    admin_notes: Optional[str] = None
    items: List[dict]


class ValidationResponse(BaseModel):
    id: int
    assignment_id: int
    validation_date: datetime
    admin_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
