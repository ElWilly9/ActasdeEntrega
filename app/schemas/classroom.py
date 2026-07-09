from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ClassroomCreate(BaseModel):
    nombre: str
    codigo: str


class ClassroomUpdate(BaseModel):
    nombre: str
    codigo: str


class ClassroomResponse(BaseModel):
    id: int
    nombre: str
    codigo: str
    created_at: datetime

    class Config:
        from_attributes = True
