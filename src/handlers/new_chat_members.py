from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from .base import BaseHandler


class NewChatMembersHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(
            MessageHandler(
                filters.StatusUpdate.NEW_CHAT_MEMBERS & filters.ChatType.GROUPS,
                self.new_chat_members,
            )
        )

    async def new_chat_members(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message = self._get_message(update)
        new_users = (
            message.new_chat_members if message.new_chat_members is not None else []
        )
        added_new_users = []
        for user in new_users:
            if user.username == "CodingQuestionsBot":
                await self._reply_text(
                    context,
                    message,
                    "You've just added the Coding Question Bot! Use /add_me to join the tracking for this chat!",
                )
            if user.is_bot:
                continue

            user_dict = self.service.user.create_if_not_exists(
                full_name=user.full_name,
                username=user.username,
                telegram_id=str(user.id),
            )
            added_new_users.append(user_dict)

        chat = self._get_chat(update)
        chat_dict = self.service.chat.create_if_not_exists(
            title=chat.title, telegram_id=str(chat.id)
        )

        for user_dict in added_new_users:
            self.service.belong.add_user_to_chat_if_not_inside(
                user_id=user_dict["id"], chat_id=chat_dict["id"]
            )
            self.helper.logger.info(
                f"Added {user_dict['full_name']} to chat {chat_dict['title']}"
            )
