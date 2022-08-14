from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

from .base import BaseHandler
from .members import MembersHandler


class AddMeHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(CommandHandler("add_me", self.add_me, filters.ChatType.GROUPS))

    async def add_me(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = self._get_chat(update)
        user = self._get_user(update)
        message = self._get_message(update)
        chat_dict = self.service.chat.create_if_not_exists(
            title=chat.title, telegram_id=str(chat.id)
        )
        user_dict = self.service.user.create_if_not_exists(
            full_name=user.full_name, username=user.username, telegram_id=str(user.id)
        )

        if self.service.belong.is_user_inside_chat(
            user_id=user_dict["id"], chat_id=chat_dict["id"]
        ):
            await self._reply_text(
                context, message, "You're already inside this chat group!"
            )
            return

        self.service.belong.add_user_to_chat_if_not_inside(
            user_id=user_dict["id"], chat_id=chat_dict["id"]
        )
        self.helper.logger.info(
            f"Added {user_dict['full_name']} to chat {chat_dict['title']}"
        )
        await self._reply_text(context, message, "Added you to this chat group!")
        await MembersHandler(self.service, self.helper, self.config).members(
            update, context
        )
