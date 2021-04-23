from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from src.config import APP_CONFIG
from src.handle_add import add_conv_handler
from src.handle_general import error_handler, start, unknown_message


def main() -> None:
    updater = Updater(APP_CONFIG["BOT_ACCESS_TOKEN"])
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(add_conv_handler)
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, unknown_message)
    )
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
