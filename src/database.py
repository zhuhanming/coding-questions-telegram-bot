import uuid
from contextlib import contextmanager

from sqlalchemy import Column, DateTime, ForeignKey, String, create_engine, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from src.config import APP_CONFIG

_base = declarative_base()


class Base(_base):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def additional_things_to_dict(self):
        return {}

    def asdict(self):
        d = {}
        columns = self.__table__.columns.keys()

        for col in columns:
            item = getattr(self, col)

            if isinstance(item, uuid.UUID):
                d[col] = str(item)
            else:
                d[col] = item

        for key, value in self.additional_things_to_dict.items():
            d[key] = value

        return d


class User(Base):
    __tablename__ = "users"

    full_name = Column(String, nullable=False)
    telegram_id = Column(String, nullable=False, unique=True)

    question_records = relationship("QuestionRecord", back_populates="user")


class QuestionRecord(Base):
    __tablename__ = "question_records"

    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String, nullable=False)
    question_name = Column(String, nullable=False)

    user = relationship("User", back_populates="question_records")


engine = create_engine(APP_CONFIG["DATABASE_URL"])
Session = sessionmaker(bind=engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
