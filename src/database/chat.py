from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .belong import Belong
    from .interview_pair import InterviewPair


class Chat(Base):
    __tablename__ = "chats"

    title = Column(String, nullable=False)
    telegram_id = Column(String, nullable=False, unique=True)

    belongs_in_chat = relationship(
        "Belong", back_populates="chat", foreign_keys="[Belong.chat_id]"
    )
    interview_pairs = relationship(
        "InterviewPair", back_populates="chat", foreign_keys="[InterviewPair.chat_id]"
    )
