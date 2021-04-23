"""
Telegram bot to support groups that wish to keep each other accountable in
LeetCoding and do mock interviews with each other.

Core functionalities:
1. User-level
    - User can add a question that they have just completed.
    - User can see the questions that they have completed this week.
    - User can see all questions that they have ever completed.
2. Group-level
    - Group can see number of questions completed by each member this week.
    - Group can see detailed list of questions completed by each member this week.
    - Group can generate pairings for mock interviews.

Design:
1. Persistence
    - Data will be persisted to a database on the server.
"""

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
