from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: str
    nombre: str
    classroom_id: Optional[int] = None


class UserUpdate(BaseModel):
    email: str
    nombre: str
    classroom_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    email: str
    nombre: str
    rol: str
    classroom_id: Optional[int] = None
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True
