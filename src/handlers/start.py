from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
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
                reply_markup=InlineKeyboardMarkup(self.get_keyboard()),
            )
            return

        self.helper.logger.info(f"User started: {user.full_name}")
        await update.message.reply_text(
            f"Hello {user.full_name}!", reply_markup=ReplyKeyboardRemove()
        )

    def get_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return [[InlineKeyboardButton(text="Get started", url=self.config["BOT_URL"])]]
