from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from ..utils import unwrap
from .base import BaseHandler


class AddQuestionHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(CallbackQueryHandler(self.add_question, "add_question"))

    async def add_question(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        query = unwrap(update.callback_query)
        user = unwrap(update.effective_user)
        await query.answer()

        self.helper.logger.info(f"User started adding question: {user.full_name}")
        await query.edit_message_text(
            f"Hi {user.full_name}! Glad to see that you've been working hard!\n"
            "Can you send me the URL of the question that you've attempted?",
            reply_markup=InlineKeyboardMarkup(self.__get_back_keyboard()),
        )

    def __get_back_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return [[InlineKeyboardButton(text="Cancel", callback_data="back")]]
