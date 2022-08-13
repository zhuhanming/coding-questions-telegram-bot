from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class QuestionRecord(Base):
    __tablename__ = "question_records"

    user_id = Column(
        UUID,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    platform = Column(String, nullable=False)
    question_name = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)

    user = relationship("User", back_populates="question_records")
