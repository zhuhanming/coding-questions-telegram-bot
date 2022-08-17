from ..database import Belong, Chat, User, session_scope
from ..utils import UUID_RULE, OptInOutType, ResourceNotFoundException, validate_input

BELONG_SCHEMA = {"user_id": UUID_RULE, "chat_id": UUID_RULE}
IS_OPTED_OUT_SCHEMA = {
    "user_id": UUID_RULE,
    "chat_id": UUID_RULE,
    "opt_in_out_type": {"required": True},
}
OPT_IN_OUT_SCHEMA = IS_OPTED_OUT_SCHEMA
GET_USERS_IN_CHAT_SCHEMA = {"chat_id": UUID_RULE}
GET_CHATS_FOR_USER_SCHEMA = {"user_id": UUID_RULE}


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

    @validate_input(GET_USERS_IN_CHAT_SCHEMA)
    def get_users_in_chat(self, chat_id: str) -> list[dict]:
        with session_scope() as session:
            user_belong_pairs: list[tuple[User, Belong]] = (
                session.query(User, Belong)
                .join(Belong, Belong.user_id == User.id)
                .filter(Belong.chat_id == chat_id)
                .all()
            )
            return [
                {
                    **u.as_dict(),
                    "is_opted_out_of_questions": b.is_opted_out_of_questions,
                    "is_opted_out_of_interviews": b.is_opted_out_of_interviews,
                }
                for (u, b) in user_belong_pairs
            ]

    @validate_input(GET_CHATS_FOR_USER_SCHEMA)
    def get_chats_for_user(self, user_id: str) -> list[dict]:
        with session_scope() as session:
            chat_belong_pairs: list[tuple[Chat, Belong]] = (
                session.query(Chat, Belong)
                .join(Belong, Belong.chat_id == Chat.id)
                .filter(Belong.user_id == user_id)
                .all()
            )
            return [c.as_dict() for (c, _) in chat_belong_pairs]

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
    def get_opt_in_out_status(
        self, user_id: str, chat_id: str
    ) -> dict[OptInOutType, bool]:
        with session_scope() as session:
            belong: Belong | None = (
                session.query(Belong)
                .filter_by(user_id=user_id, chat_id=chat_id)
                .one_or_none()
            )
            if belong is None:
                raise ResourceNotFoundException()

            return {
                OptInOutType.QUESTIONS: belong.is_opted_out_of_questions,
                OptInOutType.INTERVIEWS: belong.is_opted_out_of_interviews,
            }

    @validate_input(OPT_IN_OUT_SCHEMA)
    def toggle_opt_in_out(
        self,
        user_id: str,
        chat_id: str,
        opt_in_out_type: OptInOutType,
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
                belong.is_opted_out_of_questions = not belong.is_opted_out_of_questions
            else:
                belong.is_opted_out_of_interviews = (
                    not belong.is_opted_out_of_interviews
                )

            session.commit()
            return belong.as_dict()
