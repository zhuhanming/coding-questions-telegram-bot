from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from .base import BaseHandler


class UnknownMessageHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        # Sometimes, people reply to messages from the bot in a group setting. We will just ignore such cases
        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
                self.unknown_message,
            )
        )

    async def unknown_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await self._clear_previous_message_reply_markup(update, context)
        await self._reply_text(
            context,
            self._get_message(update),
            "Unfortunately, I don't recognise this command!\n\n"
            "How else can I help you?",
            self.__get_keyboard(),
        )

    def __get_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Add a question", callback_data="add_question"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Complete an interview", callback_data="complete_interview"
                    )
                ],
                [InlineKeyboardButton(text="View stats", callback_data="view_stats")],
            ]
        )
