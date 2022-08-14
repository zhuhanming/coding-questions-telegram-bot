from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from .base import BaseHandler


class UnknownMessageHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown_message)
        )

    async def unknown_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if self._get_chat(update).type != "private":
            # Sometimes, people reply to messages from the bot in a group setting.
            # We will just ignore such cases and pretend we didn't receive any commands.
            return

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
