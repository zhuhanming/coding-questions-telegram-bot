from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .chat import Chat
    from .user import User


class Belong(Base):
    __tablename__ = "belongs"

    user_id = Column(
        UUID,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    chat_id = Column(
        UUID,
        ForeignKey("chats.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    is_opted_out = Column(Boolean, nullable=False, server_default="f")

    chat = relationship(
        "Chat", back_populates="belongs_in_chat", foreign_keys=[chat_id]
    )
    user = relationship(
        "User", back_populates="user_belongs_in", foreign_keys=[user_id]
    )

    __table_args__ = (UniqueConstraint("user_id", "chat_id"),)
