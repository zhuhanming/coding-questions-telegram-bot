from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from .base import BaseHandler


class ChatCreatedHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(
            MessageHandler(
                filters.StatusUpdate.CHAT_CREATED & filters.ChatType.GROUPS,
                self.chat_created,
            )
        )

    async def chat_created(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message = self._get_message(update)
        chat = self._get_chat(update)

        chat_dict = self.service.chat.create_if_not_exists(
            title=chat.title, telegram_id=str(chat.id)
        )
        user = message.from_user

        if user is not None and not user.is_bot:
            user_dict = self.service.user.create_if_not_exists(
                full_name=user.full_name,
                username=user.username,
                telegram_id=str(user.id),
            )
            self.service.belong.add_user_to_chat_if_not_inside(
                user_id=user_dict["id"], chat_id=chat_dict["id"]
            )

        self.helper.logger.info(f"Added to chat {chat_dict['title']}")
        await self._reply_text(
            context,
            message,
            "You've just added the Coding Question Bot! Use /add_me to join the tracking for this chat!",
        )
