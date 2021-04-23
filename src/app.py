from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from src.add import add_conv_handler
from src.config import APP_CONFIG
from src.error import error_handler
from src.general import start, unknown_message


def main() -> None:
    """Starts the bot."""
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
