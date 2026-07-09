import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models import Base
from app.tz import local_now


class Condicion(str, enum.Enum):
    """Condicion de un activo: Malo / Regular / Bueno (columnas M/R/B de la plantilla)."""

    malo = "Malo"
    regular = "Regular"
    bueno = "Bueno"


class Assignment(Base):
    """Acta de Entrega: pertenece a un salon y agrupa los activos entregados."""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    titulo = Column(String(255), nullable=False)
    assignment_date = Column(DateTime, default=local_now)
    active = Column(Boolean, default=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=local_now)

    classroom = relationship("Classroom", back_populates="assignments")
    user = relationship("User", back_populates="assignments")
    items = relationship("AssignmentItem", back_populates="assignment", cascade="all, delete-orphan")
    validations = relationship("Validation", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentItem(Base):
    """Linea del acta: un activo con su cantidad, serial, condicion y observacion."""

    __tablename__ = "assignment_items"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    descripcion = Column(String(255), nullable=False)
    serial = Column(String(100), nullable=True)
    estado = Column(Enum(Condicion), nullable=False, default=Condicion.bueno)
    observacion = Column(Text, nullable=True)

    assignment = relationship("Assignment", back_populates="items")


class Validation(Base):
    """Acta de Devolucion: re-chequeo de los activos de un acta de entrega."""

    __tablename__ = "validations"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    validation_date = Column(DateTime, default=local_now)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=local_now)

    assignment = relationship("Assignment", back_populates="validations")
    items = relationship("ValidationItem", back_populates="validation", cascade="all, delete-orphan")


class ValidationItem(Base):
    """Re-chequeo de una linea: si se devolvio, en que condicion y observacion."""

    __tablename__ = "validation_items"

    id = Column(Integer, primary_key=True, index=True)
    validation_id = Column(Integer, ForeignKey("validations.id"), nullable=False)
    assignment_item_id = Column(Integer, ForeignKey("assignment_items.id"), nullable=False)
    devuelto = Column(Boolean, default=True)
    estado = Column(Enum(Condicion), nullable=True)
    observacion = Column(Text, nullable=True)

    validation = relationship("Validation", back_populates="items")
    assignment_item = relationship("AssignmentItem")
