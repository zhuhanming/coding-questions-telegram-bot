from telegram import ForceReply, Update
from telegram.ext import CallbackContext

from src.logger import logger


def start(update: Update, _: CallbackContext) -> None:
    """Sends a default welcome message when the /start command is issued"""
    user = update.effective_user
    logger.info("User started: %s %s", user.id, user.full_name)
    update.message.reply_markdown_v2(
        fr"Hi {user.mention_markdown_v2()}\!", reply_markup=ForceReply(selective=True)
    )
