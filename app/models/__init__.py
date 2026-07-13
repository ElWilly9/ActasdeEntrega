from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from app.models.user import User  # noqa
from app.models.classroom import Classroom  # noqa
from app.models.assignment import (  # noqa
    Assignment,
    AssignmentItem,
    Validation,
    ValidationExtraItem,
    ValidationItem,
)
