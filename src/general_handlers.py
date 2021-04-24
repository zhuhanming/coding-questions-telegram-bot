import html
import json
import traceback

from telegram import ForceReply, ParseMode, Update
from telegram.ext import CallbackContext

from src.config import APP_CONFIG
from src.services import SERVICES


def start(update: Update, _: CallbackContext) -> None:
    """Sends a default welcome message when the /start command is issued"""
    user = update.effective_user
    SERVICES.logger.info("User started: %s %s", user.id, user.full_name)
    update.message.reply_markdown_v2(
        fr"Hi {user.mention_markdown_v2()}\!", reply_markup=ForceReply(selective=True)
    )


def unknown_message(update: Update, _: CallbackContext) -> None:
    """Sends a default message when an unknown command was issued"""
    update.message.reply_text("Unfortunately, I don't recognise this command!")


def error_handler(update: Update, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    SERVICES.logger.error(
        msg="Exception while handling an update:", exc_info=context.error
    )

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)[: APP_CONFIG["TRACEBACK_LENGTH"]]

    # Build the message with some markup and additional information about what happened.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    context.bot.send_message(
        chat_id=APP_CONFIG["DEVELOPER_ID"], text=message, parse_mode=ParseMode.HTML
    )


def new_chat_member_handler(update: Update, context: CallbackContext) -> None:
    print(update)
    print(context)