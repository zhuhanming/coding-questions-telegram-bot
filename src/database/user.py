from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .belong import Belong
    from .interview_pair import InterviewPair
    from .question_record import QuestionRecord


class User(Base):
    __tablename__ = "users"

    full_name = Column(String, nullable=False)
    telegram_id = Column(String, nullable=False, unique=True)

    question_records = relationship("QuestionRecord", back_populates="user")
    user_belongs_in = relationship(
        "Belong", back_populates="user", foreign_keys="[Belong.user_id]"
    )
    interview_pairs_as_user_one = relationship(
        "InterviewPair",
        back_populates="user_one",
        foreign_keys="[InterviewPair.user_one_id]",
    )
    interview_pairs_as_user_two = relationship(
        "InterviewPair",
        back_populates="user_two",
        foreign_keys="[InterviewPair.user_two_id]",
    )
