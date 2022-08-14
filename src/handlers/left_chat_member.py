from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from ..utils import ResourceNotFoundException
from .base import BaseHandler


class LeftChatMemberHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(
            MessageHandler(
                filters.StatusUpdate.LEFT_CHAT_MEMBER & filters.ChatType.GROUPS,
                self.left_chat_member,
            )
        )

    async def left_chat_member(
        self, update: Update, _: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message = self._get_message(update)
        if message.left_chat_member is None:
            return
        chat = self._get_chat(update)
        user = message.left_chat_member

        try:
            user_dict = self.service.user.get_user_by_telegram_id(
                telegram_id=str(user.id)
            )
            chat_dict = self.service.chat.get_chat_by_telegram_id(
                telegram_id=str(chat.id)
            )
            self.service.belong.remove_user_from_chat_if_inside(
                user_id=user_dict["id"], chat_id=chat_dict["id"]
            )
            self.helper.logger.info(
                f"Removed {user_dict['full_name']} from chat {chat_dict['title']}"
            )
        except ResourceNotFoundException:
            # User did not exist in the group. Fail silently.
            return
