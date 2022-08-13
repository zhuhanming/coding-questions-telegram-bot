from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .chat import Chat
    from .user import User


class InterviewPair(Base):
    __tablename__ = "interview_pairs"

    user_one_id = Column(
        UUID,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    user_two_id = Column(
        UUID,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    chat_id = Column(
        UUID,
        ForeignKey("chats.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    started_at = Column(DateTime(timezone=True), nullable=False)
    is_completed = Column(Boolean, nullable=False, server_default="f")
    completed_at = Column(DateTime(timezone=True))

    user_one = relationship(
        "User", back_populates="interview_pairs_as_user_one", foreign_keys=[user_one_id]
    )
    user_two = relationship(
        "User", back_populates="interview_pairs_as_user_two", foreign_keys=[user_two_id]
    )
    chat = relationship(
        "Chat", back_populates="interview_pairs", foreign_keys=[chat_id]
    )

    @property
    def additional_things_to_dict(self):
        return {
            "user_one_name": self.user_one.full_name,
            "user_two_name": self.user_two.full_name,
            "chat_title": self.chat.title,
        }
