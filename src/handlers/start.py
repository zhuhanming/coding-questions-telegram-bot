from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .base import BaseHandler


class StartHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(CommandHandler("start", self.start))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = self._get_user(update)
        message = self._get_message(update)

        if self._get_chat(update).type != "private":
            await self._reply_text(
                context,
                message,
                "Get started with coding question practice now!",
                self.__get_redirect_keyboard(),
            )
            return

        self.helper.logger.info(f"User started: {user.full_name}")
        await self._reply_text(
            context,
            message,
            f"Hello {user.full_name}! What do you want to do today?",
            self.__get_private_chat_keyboard(),
        )

    def __get_redirect_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Start a conversation with me!", url=self.config["BOT_URL"]
                    )
                ]
            ]
        )

    def __get_private_chat_keyboard(self) -> InlineKeyboardMarkup:
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
