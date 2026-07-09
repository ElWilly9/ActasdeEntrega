import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models import Base
from app.tz import local_now


class UserRole(str, enum.Enum):
    admin = "admin"
    profesor = "profesor"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(Enum(UserRole), nullable=False, default=UserRole.profesor)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=local_now)

    classroom = relationship("Classroom", back_populates="users")
    assignments = relationship("Assignment", back_populates="user")
