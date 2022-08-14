from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

from .base import BaseHandler


class MembersHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(
            CommandHandler("members", self.members, filters.ChatType.GROUPS)
        )

    async def members(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = self._get_message(update)
        chat = self._get_chat(update)
        chat_dict = self.service.chat.get_chat_by_telegram_id(telegram_id=str(chat.id))
        user_dicts = self.service.belong.get_users_in_chat(chat_id=chat_dict["id"])

        if not user_dicts:
            await self._reply_text(
                context,
                message,
                "There are no members in this chat!\n\n"
                "Please add yourself with the /add_me command.",
            )

        header_text = f"Members in {chat_dict['title']}"
        user_dicts.sort(key=lambda x: str(x["full_name"]).lower())
        items = [self.__user_dict_mapper(user_dict) for user_dict in user_dicts]
        pagination = self.helper.pagination.create_and_set_data(header_text, items, 20)
        text, keyboard = pagination.generate_message(0)
        await self._reply_text(context, message, text, keyboard)

    def __user_dict_mapper(self, user: dict) -> str:
        result = str(user["full_name"])
        if user["is_opted_out_of_questions"] and user["is_opted_out_of_interviews"]:
            result += " (Opted Out of Questions & Interviews)"
        elif user["is_opted_out_of_questions"]:
            result += " (Opted Out of Questions)"
        elif user["is_opted_out_of_interviews"]:
            result += " (Opted Out of Interviews)"
        return result
