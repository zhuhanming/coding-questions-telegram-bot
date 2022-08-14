from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from ..utils import unwrap
from .base import BaseHandler


class StartHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(CommandHandler("start", self.start))

    async def start(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        user = unwrap(update.effective_user)
        update.message = unwrap(update.message)

        if update.message.chat.type != "private":
            await update.message.reply_text(
                "Get started with coding question practice now!",
                reply_markup=InlineKeyboardMarkup(self.__get_redirect_keyboard()),
            )
            return

        self.helper.logger.info(f"User started: {user.full_name}")
        await update.message.reply_text(
            f"Hello {user.full_name}! What do you want to do today?",
            reply_markup=InlineKeyboardMarkup(self.__get_private_chat_keyboard()),
        )

    def __get_redirect_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return [
            [
                InlineKeyboardButton(
                    text="Start a conversation with me!", url=self.config["BOT_URL"]
                )
            ]
        ]

    def __get_private_chat_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return [
            [InlineKeyboardButton(text="Add a question", callback_data="add_question")],
            [
                InlineKeyboardButton(
                    text="Complete an interview", callback_data="complete_interview"
                )
            ],
            [InlineKeyboardButton(text="View stats", callback_data="view_stats")],
        ]
