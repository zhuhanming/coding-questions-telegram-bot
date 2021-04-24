from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from src.add_handlers import add_conv_handler
from src.config import APP_CONFIG
from src.general_handlers import (
    error_handler,
    new_chat_member_handler,
    start,
    unknown_message,
)
from src.stats_handlers import week


def main() -> None:
    updater = Updater(APP_CONFIG["BOT_ACCESS_TOKEN"])
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("week", week))
    dispatcher.add_handler(add_conv_handler)
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, unknown_message)
    )
    dispatcher.add_handler(
        MessageHandler(Filters.status_update.new_chat_members, new_chat_member_handler)
    )
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
