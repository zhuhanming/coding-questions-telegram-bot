from ..database import Belong, User, session_scope
from ..utils import UUID_RULE, OptInOutType, ResourceNotFoundException, validate_input

BELONG_SCHEMA = {"user_id": UUID_RULE, "chat_id": UUID_RULE}
IS_OPTED_OUT_SCHEMA = {
    "user_id": UUID_RULE,
    "chat_id": UUID_RULE,
    "opt_in_out_type": {"required": True},
}
OPT_IN_OUT_SCHEMA = {
    "user_id": UUID_RULE,
    "chat_id": UUID_RULE,
    "should_opt_out": {"type": "boolean", "required": True},
    "opt_in_out_type": {"required": True},
}


class BelongService:
    @validate_input(BELONG_SCHEMA)
    def add_user_to_chat_if_not_inside(self, user_id: str, chat_id: str) -> dict:
        with session_scope() as session:
            belong: Belong | None = (
                session.query(Belong)
                .filter_by(user_id=user_id, chat_id=chat_id)
                .one_or_none()
            )
            if belong is None:
                belong = Belong(user_id=user_id, chat_id=chat_id)
                session.add(belong)
                session.flush()

            session.commit()
            return belong.as_dict()

    @validate_input(BELONG_SCHEMA)
    def remove_user_from_chat_if_inside(self, user_id: str, chat_id: str) -> bool:
        with session_scope() as session:
            belong = (
                session.query(Belong)
                .filter_by(user_id=user_id, chat_id=chat_id)
                .one_or_none()
            )
            if belong is not None:
                session.delete(belong)

            session.commit()
            return belong is not None

    @validate_input({"chat_id": UUID_RULE})
    def get_users_in_chat(self, chat_id: str) -> list[dict]:
        with session_scope() as session:
            user_belong_pairs = (
                session.query(User, Belong)
                .join(Belong, Belong.user_id == User.id)
                .filter(Belong.chat_id == chat_id)
                .all()
            )
            return [
                {**u.as_dict(), "is_opted_out": b.is_opted_out}
                for (u, b) in user_belong_pairs
            ]

    @validate_input(BELONG_SCHEMA)
    def is_user_inside_chat(self, user_id: str, chat_id: str) -> bool:
        with session_scope() as session:
            belong = (
                session.query(Belong)
                .filter_by(user_id=user_id, chat_id=chat_id)
                .one_or_none()
            )
            return belong is not None

    @validate_input(BELONG_SCHEMA)
    def is_user_opted_out(
        self, user_id: str, chat_id: str, opt_in_out_type: OptInOutType
    ) -> bool:
        with session_scope() as session:
            belong: Belong | None = (
                session.query(Belong)
                .filter_by(user_id=user_id, chat_id=chat_id)
                .one_or_none()
            )
            if belong is None:
                raise ResourceNotFoundException()
            if opt_in_out_type == OptInOutType.QUESTIONS:
                return belong.is_opted_out_of_questions
            return belong.is_opted_out_of_interviews

    @validate_input(OPT_IN_OUT_SCHEMA)
    def opt_in_out(
        self,
        user_id: str,
        chat_id: str,
        opt_in_out_type: OptInOutType,
        should_opt_out: bool,
    ) -> dict:
        with session_scope() as session:
            belong: Belong | None = (
                session.query(Belong)
                .filter_by(user_id=user_id, chat_id=chat_id)
                .one_or_none()
            )
            if belong is None:
                raise ResourceNotFoundException()

            if opt_in_out_type == OptInOutType.QUESTIONS:
                belong.is_opted_out_of_questions = should_opt_out
            else:
                belong.is_opted_out_of_interviews = should_opt_out

            session.commit()
            return belong.as_dict()
