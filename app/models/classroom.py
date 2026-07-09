from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.models import Base
from app.tz import local_now


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=local_now)

    users = relationship("User", back_populates="classroom")
    assignments = relationship("Assignment", back_populates="classroom")
