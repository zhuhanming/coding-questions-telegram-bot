import html
import json
import traceback
from typing import cast

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes

from .base import BaseHandler


class ErrorHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_error_handler(self.error)

    async def error(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        # Log the error before we do anything else, so we can see it even if something breaks.
        self.helper.logger.error(
            msg="Exception while handling an update:", exc_info=context.error
        )
        error = self._get_error(context)

        # traceback.format_exception returns the usual python message about an exception, but as a
        # list of strings rather than a single string, so we have to join them together.
        tb_list = traceback.format_exception(None, error, error.__traceback__)
        tb_string = "".join(tb_list)

        # Build the message with some markup and additional information about what happened.
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            f"An exception was raised while handling an update\n"
            f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
            "</pre>\n\n"
            f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
            f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        )
        await context.bot.send_message(
            chat_id=self.config["DEVELOPER_ID"], text=message, parse_mode=ParseMode.HTML
        )

        for i in range(len(tb_string) // self.config["TRACEBACK_LENGTH"] + 1):
            tb_segment = tb_string[
                (i * self.config["TRACEBACK_LENGTH"]) : (
                    (i + 1) * self.config["TRACEBACK_LENGTH"]
                )
            ]
            if not tb_segment:
                continue
            message = f"<pre>{html.escape(tb_segment)}</pre>"
            await context.bot.send_message(
                chat_id=self.config["DEVELOPER_ID"],
                text=message,
                parse_mode=ParseMode.HTML,
            )

        casted_update = cast(Update, update)
        if casted_update is None or casted_update.message is None:
            return

        await self._clear_previous_message_reply_markup(casted_update, context)
        await self._reply_text(
            context,
            casted_update.message,
            "Uh oh, something went wrong! I've already informed my developer about this.",
        )
