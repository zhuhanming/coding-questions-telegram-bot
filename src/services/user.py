from ..database import User, session_scope
from ..utils import UUID_RULE, UUIDS_RULE, ResourceNotFoundException, validate_input

TELEGRAM_USER_ID_REGEX = "^[0-9]+$"
TELEGRAM_USER_ID_RULE = {"type": "string", "regex": TELEGRAM_USER_ID_REGEX}
CREATE_USER_SCHEMA = {
    "full_name": {"type": "string"},
    "telegram_id": TELEGRAM_USER_ID_RULE,
}
GET_USER_SCHEMA = {"telegram_id": TELEGRAM_USER_ID_RULE}


class UserService:
    @validate_input(CREATE_USER_SCHEMA)
    def create_if_not_exists(self, full_name: str, telegram_id: str) -> dict:
        with session_scope() as session:
            user: User | None = (
                session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
            )
            if user is None:
                user = User(full_name=full_name, telegram_id=telegram_id)
                session.add(user)
                session.flush()
            else:
                user.full_name = full_name

            session.commit()
            return user.as_dict()

    @validate_input(GET_USER_SCHEMA)
    def get_user_by_telegram_id(self, telegram_id: str) -> dict:
        with session_scope() as session:
            user: User | None = (
                session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
            )
            if user is None:
                raise ResourceNotFoundException()
            return user.as_dict()

    @validate_input({"id": UUID_RULE})
    def get_user_by_id(self, id: str) -> dict:
        with session_scope() as session:
            user: User | None = session.query(User).filter_by(id=id).one_or_none()
            if user is None:
                raise ResourceNotFoundException()
            return user.as_dict()

    @validate_input({"ids": UUIDS_RULE})
    def get_users_by_id(self, ids: list[str]) -> list[dict]:
        with session_scope() as session:
            users: list[User] = session.query(User).filter(User.id.in_(ids)).all()
            if len(users) != len(ids):
                raise ResourceNotFoundException()
            return [user.as_dict() for user in users]
