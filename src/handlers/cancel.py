from telegram import ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from ..utils import unwrap
from .base import BaseHandler


class CancelHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(CommandHandler("cancel", self.cancel))

    async def cancel(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        update.message = unwrap(update.message)
        await update.message.reply_text(
            "You have no ongoing operation to cancel.",
            reply_markup=ReplyKeyboardRemove(),
        )
