from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from src.add_handlers import add_conv_handler
from src.chat_handlers import (
    add_me,
    chat_members,
    left_chat_member_handler,
    new_chat_member_handler,
)
from src.config import APP_CONFIG
from src.general_handlers import error_handler, start, unknown_message
from src.stats_handlers import all_questions, all_unique, month, week


def main() -> None:
    updater = Updater(APP_CONFIG["BOT_ACCESS_TOKEN"])
    dispatcher = updater.dispatcher

    # Individual commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("week", week))
    dispatcher.add_handler(CommandHandler("month", month))
    dispatcher.add_handler(CommandHandler("all", all_questions))
    dispatcher.add_handler(CommandHandler("all_unique", all_unique))
    dispatcher.add_handler(add_conv_handler)

    # Group commands
    dispatcher.add_handler(CommandHandler("members", chat_members))
    dispatcher.add_handler(CommandHandler("add_me", add_me))

    # General handlers
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, unknown_message)
    )
    dispatcher.add_handler(
        MessageHandler(Filters.status_update.new_chat_members, new_chat_member_handler)
    )
    dispatcher.add_handler(
        MessageHandler(Filters.status_update.left_chat_member, left_chat_member_handler)
    )
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
