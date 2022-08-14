from ..database import Chat, session_scope
from ..utils import ResourceNotFoundException, validate_input

CREATE_CHAT_SCHEMA = {"title": {"type": "string"}, "telegram_id": {"type": "string"}}
GET_CHAT_SCHEMA = {"telegram_id": {"type": "string"}}
MIGRATE_CHAT_SCHEMA = {
    "old_telegram_id": {"type": "string"},
    "new_telegram_id": {"type": "string"},
}


class ChatService:
    @validate_input(CREATE_CHAT_SCHEMA)
    def create_if_not_exists(self, title: str, telegram_id: str) -> dict:
        with session_scope() as session:
            chat: Chat | None = (
                session.query(Chat).filter_by(telegram_id=telegram_id).one_or_none()
            )
            if chat is None:
                chat = Chat(title=title, telegram_id=telegram_id)
                session.add(chat)
                session.flush()
            else:
                chat.title = title

            session.commit()
            return chat.as_dict()

    @validate_input(GET_CHAT_SCHEMA)
    def get_chat_by_telegram_id(self, telegram_id: str) -> dict:
        with session_scope() as session:
            chat: Chat | None = (
                session.query(Chat).filter_by(telegram_id=telegram_id).one_or_none()
            )
            if chat is None:
                raise ResourceNotFoundException()
            return chat.as_dict()

    # There are times where the chat ID actually changes due to e.g. upgrading to a supergroup.
    @validate_input(MIGRATE_CHAT_SCHEMA)
    def migrate_chat_telegram_id(
        self, old_telegram_id: str, new_telegram_id: str
    ) -> dict:
        with session_scope() as session:
            chat: Chat | None = (
                session.query(Chat).filter_by(telegram_id=old_telegram_id).one_or_none()
            )
            if chat is None:
                raise ResourceNotFoundException()

            chat.telegram_id = new_telegram_id

            session.commit()
            return chat.as_dict()
