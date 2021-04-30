from typing import Optional

from telegram import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.error import Unauthorized
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
)
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton

from src.config import APP_CONFIG
from src.services import SERVICES
from src.utils import generate_weekly_summary

URL, CONFIRM, MANUAL, THANKS = range(4)
PLATFORMS = ["leetcode", "hackerrank"]
ADD_KEYBOARD = [["LeetCode", "HackerRank", "Other"]]
CONFIRM_KEYBOARD = [["Yes", "No"]]
GET_STARTED_KEYBOARD = [
    [InlineKeyboardButton(text="Get started", url=APP_CONFIG["BOT_URL"])]
]


def add(update: Update, context: CallbackContext) -> Optional[int]:
    """Kicks off the question adding process and asks user for the platform used."""
    user = update.effective_user

    if update.message.chat.type != "private":
        try:
            context.bot.send_message(
                chat_id=user.id, text="Please resend /add_question here again!"
            )
        except Unauthorized:
            update.message.reply_text(
                "You need to start a conversation with me first!",
                reply_markup=InlineKeyboardMarkup(GET_STARTED_KEYBOARD),
            )
        return

    update.message.reply_text(
        "Hi {}! Glad to see that you've been working hard!\n".format(user.full_name)
        + "If you don't mind me asking, what platform did you use?\n"
        "You can also send /cancel to cancel.",
        reply_markup=ReplyKeyboardMarkup(ADD_KEYBOARD, one_time_keyboard=True),
    )
    return URL


def url(update: Update, context: CallbackContext) -> int:
    """Acknowledges the platform selected and asks for the URL from the user."""
    platform = update.message.text.lower()
    assert platform in PLATFORMS

    context.user_data[APP_CONFIG["PLATFORM_KEY"]] = platform
    update.message.reply_text(
        "Please send me the URL of the question you just attempted!\n"
        "You can also send /cancel to cancel.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return CONFIRM


def other(update: Update, context: CallbackContext) -> int:
    """Handles the case where the user selects Other."""
    platform = update.message.text.lower()
    assert platform == "other"
    context.user_data[APP_CONFIG["PLATFORM_KEY"]] = platform
    update.message.reply_text(
        "Do you mind letting me know what the name of the question you attempted was?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return MANUAL


def confirm(update: Update, context: CallbackContext) -> int:
    """Fetches the question title and confirms it with the user."""
    url = update.message.text.lower()
    platform = context.user_data.get(APP_CONFIG["PLATFORM_KEY"])

    assert platform in PLATFORMS
    update.message.reply_text(
        "This part may take a while to load.\n" "Do be patient with me!"
    )
    is_leetcode = platform == "leetcode"

    question_name = (
        SERVICES.question_name_service.get_leetcode_question_name(url=url)
        if is_leetcode
        else SERVICES.question_name_service.get_hackerrank_question_name(url=url)
    )

    if question_name is None or not question_name:
        best_effort_question_name = (
            SERVICES.question_name_service.parse_leetcode_url_directly(url=url)
            if is_leetcode
            else SERVICES.question_name_service.parse_hackerank_url_directly(url=url)
        )

        if best_effort_question_name is None:
            update.message.reply_text(
                "It seems like either the URL is invalid or you sent me a premium question!\n"
                "Please enter the name of the question manually. "
                "You can also send /cancel to cancel and restart this process.",
                reply_markup=ReplyKeyboardRemove(),
            )

            return MANUAL

        update.message.reply_text(
            "I couldn't get the question title from the website directly!\n"
            "Is your question title: {}?".format(best_effort_question_name),
            reply_markup=ReplyKeyboardMarkup(CONFIRM_KEYBOARD, one_time_keyboard=True),
        )

        context.user_data[APP_CONFIG["QUESTION_NAME_KEY"]] = best_effort_question_name
        return THANKS

    update.message.reply_text(
        "I managed to find the question title from the website directly!\n"
        "Is your question title: {}?".format(question_name),
        reply_markup=ReplyKeyboardMarkup(CONFIRM_KEYBOARD, one_time_keyboard=True),
    )

    context.user_data[APP_CONFIG["QUESTION_NAME_KEY"]] = question_name
    return THANKS


def manual(update: Update, context: CallbackContext) -> int:
    """Acknowledges the manual entry and confirms it with the user."""
    question_name = update.message.text
    update.message.reply_text(
        "Just to confirm, is your question title: {}?".format(question_name),
        reply_markup=ReplyKeyboardMarkup(CONFIRM_KEYBOARD, one_time_keyboard=True),
    )

    context.user_data[APP_CONFIG["QUESTION_NAME_KEY"]] = question_name
    return THANKS


def thanks(update: Update, context: CallbackContext) -> int:
    """Acknowledges the confirmation and persists the data into the database."""

    confirmation = update.message.text.lower()

    if confirmation == "no":
        update.message.reply_text(
            "Sorry that I got your question title wrong!\n"
            "Do you mind sending the name of the question here?\n"
            "Or send /cancel to cancel."
        )
        del context.user_data[APP_CONFIG["QUESTION_NAME_KEY"]]
        return MANUAL

    user = update.effective_user
    platform = context.user_data.get(APP_CONFIG["PLATFORM_KEY"])
    question_name = context.user_data.get(APP_CONFIG["QUESTION_NAME_KEY"])

    # Persist data to database
    user = SERVICES.user_service.create_if_not_exists(
        full_name=user.full_name, telegram_id=str(user.id)
    )
    SERVICES.question_record_service.create_question_record(
        user_id=user["id"], platform=platform, question_name=question_name
    )

    SERVICES.logger.info(
        "User (%s, %s) added question: %s [%s]",
        user["telegram_id"],
        user["full_name"],
        question_name,
        platform,
    )

    context.user_data.clear()
    update.message.reply_text(
        "Awesome! Good job with the question!", reply_markup=ReplyKeyboardRemove()
    )

    records = SERVICES.question_record_service.get_records_by_user_for_this_week(
        user_id=user["id"]
    )

    summary = generate_weekly_summary(records)
    update.message.reply_text(summary)
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Fallback that ends the conversation and clears any cached data."""
    update.message.reply_text(
        "No worries! Come back again soon!", reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END


add_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("add_question", add)],
    states={
        URL: [
            MessageHandler(Filters.regex("^(LeetCode|HackerRank)$"), url),
            MessageHandler(Filters.regex("^(Other)$"), other),
            CommandHandler("cancel", cancel),
        ],
        CONFIRM: [
            MessageHandler(Filters.text & ~Filters.command, confirm),
            CommandHandler("cancel", cancel),
        ],
        MANUAL: [MessageHandler(Filters.text & ~Filters.command, manual)],
        THANKS: [
            MessageHandler(Filters.regex("^(Yes|No)$"), thanks),
            CommandHandler("cancel", cancel),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
