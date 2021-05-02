from typing import Optional

from telegram import (
    InlineKeyboardMarkup,
    ParseMode,
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
from src.exceptions import InvalidUserDataException
from src.services import SERVICES
from src.stats_handlers import SummaryType, generate_individual_summary
from src.utils import unwrap

URL, CONFIRM, MANUAL_NAME, MANUAL_DIFFICULTY_PRE, MANUAL_DIFFICULTY, THANKS = range(6)
PLATFORMS = ["leetcode", "hackerrank"]
ADD_KEYBOARD = [["LeetCode", "HackerRank", "Other"]]
DIFFICULTY_KEYBOARD = [["Easy", "Medium", "Hard"]]
CONFIRM_KEYBOARD = [["Yes", "No"]]
GET_STARTED_KEYBOARD = [
    [InlineKeyboardButton(text="Get started", url=APP_CONFIG["BOT_URL"])]
]


def add(update: Update, context: CallbackContext) -> Optional[int]:
    """Kicks off the question adding process and asks user for the platform used."""
    # Unwrap and fail fast
    user = unwrap(update.effective_user)
    update.message = unwrap(update.message)

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
        finally:
            return ConversationHandler.END

    update.message.reply_text(
        "Hi {}! Glad to see that you've been working hard!\n".format(user.full_name)
        + "If you don't mind me asking, what platform did you use?\n"
        "You can also send /cancel to cancel.",
        reply_markup=ReplyKeyboardMarkup(ADD_KEYBOARD, one_time_keyboard=True),
    )
    return URL


def url(update: Update, context: CallbackContext) -> int:
    """Acknowledges the platform selected and asks for the URL from the user."""
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    if context.user_data is None:
        raise InvalidUserDataException()

    platform = unwrap(update.message.text).lower()
    assert platform in PLATFORMS

    context.user_data["PLATFORM"] = platform
    update.message.reply_text(
        "Please send me the URL of the question you just attempted!\n"
        "You can also send /cancel to cancel.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return CONFIRM


def other(update: Update, context: CallbackContext) -> int:
    """Handles the case where the user selects Other."""
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    update.message.text = unwrap(update.message.text)
    if context.user_data is None:
        raise InvalidUserDataException()

    platform = update.message.text.lower()
    assert platform == "other"

    context.user_data["PLATFORM"] = platform
    update.message.reply_text(
        "Do you mind letting me know what the name of the question you attempted was?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return MANUAL_NAME


def confirm(update: Update, context: CallbackContext) -> int:
    """Fetches the question title and confirms it with the user."""
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    update.message.text = unwrap(update.message.text)
    if context.user_data is None:
        raise InvalidUserDataException()

    url = update.message.text.lower()
    platform = context.user_data.get("PLATFORM")

    assert platform in PLATFORMS
    if platform not in url:
        update.message.reply_text(
            "Are you sure this is a link for the platform you stated?"
            "Please send the url again!\n"
            "Or send /cancel to cancel."
        )
        return CONFIRM

    update.message.reply_text(
        "This part may take a while to load.\n" "Do be patient with me!"
    )
    is_leetcode = platform == "leetcode"

    question_info = SERVICES.question_info_service.get_question_info(
        url=url, is_leetcode=is_leetcode
    )
    context.user_data["QUESTION_NAME"] = question_info.name
    context.user_data["QUESTION_DIFFICULTY"] = (
        question_info.difficulty.lower()
        if question_info.difficulty is not None
        else None
    )

    if question_info.name is None:
        update.message.reply_text(
            "It seems like either the URL is invalid or you sent me a premium question!\n"
            "Please enter the name of the question manually. "
            "You can also send /cancel to cancel and restart this process.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return MANUAL_NAME

    if question_info.difficulty is None:
        update.message.reply_text(
            "I tried my best to get the question title from the website directly!\n"
            "Is your question title: {}?".format(question_info.name),
            reply_markup=ReplyKeyboardMarkup(CONFIRM_KEYBOARD, one_time_keyboard=True),
        )
        return MANUAL_DIFFICULTY_PRE

    assert question_info.name is not None
    assert question_info.difficulty is not None

    update.message.reply_text(
        "I managed to find the question info from the website directly!\n"
        "Is your question: {} [{}]?".format(
            question_info.name, question_info.difficulty.title()
        ),
        reply_markup=ReplyKeyboardMarkup(CONFIRM_KEYBOARD, one_time_keyboard=True),
    )

    return THANKS


def manual_name(update: Update, context: CallbackContext) -> int:
    """Acknowledges the manual name entry and confirms it with the user."""
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    update.message.text = unwrap(update.message.text)
    if context.user_data is None:
        raise InvalidUserDataException()

    question_name = update.message.text
    context.user_data["QUESTION_NAME"] = question_name

    update.message.reply_text(
        "What is the difficulty of your question?",
        reply_markup=ReplyKeyboardMarkup(DIFFICULTY_KEYBOARD, one_time_keyboard=True),
    )
    return MANUAL_DIFFICULTY


def manual_difficulty_pre(update: Update, context: CallbackContext) -> int:
    """Acknowledges the confirmation of the question name and asks for the difficulty."""
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    update.message.text = unwrap(update.message.text)
    if context.user_data is None:
        raise InvalidUserDataException()

    confirmation = update.message.text.lower()
    if confirmation == "no":
        update.message.reply_text(
            "Sorry that I got your question title wrong!\n"
            "Do you mind sending the name of the question here?\n"
            "Or send /cancel to cancel."
        )
        return MANUAL_NAME

    update.message.reply_text(
        "Awesome! What is the difficulty of the question?",
        reply_markup=ReplyKeyboardMarkup(DIFFICULTY_KEYBOARD, one_time_keyboard=True),
    )
    return MANUAL_DIFFICULTY


def manual_difficulty(update: Update, context: CallbackContext) -> int:
    """Acknowledges the manual difficulty entry and confirms it with the user."""
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    update.message.text = unwrap(update.message.text)
    if context.user_data is None:
        raise InvalidUserDataException()

    question_difficulty = update.message.text.lower()
    context.user_data["QUESTION_DIFFICULTY"] = question_difficulty
    question_name = context.user_data["QUESTION_NAME"]

    assert question_name is not None
    assert question_difficulty is not None

    update.message.reply_text(
        "Just to confirm, is your question: {} [{}]?".format(
            question_name, question_difficulty.title()
        ),
        reply_markup=ReplyKeyboardMarkup(CONFIRM_KEYBOARD, one_time_keyboard=True),
    )
    return THANKS


def thanks(update: Update, context: CallbackContext) -> int:
    """Acknowledges the confirmation and persists the data into the database."""
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    update.message.text = unwrap(update.message.text)
    user = unwrap(update.effective_user)
    if context.user_data is None:
        raise InvalidUserDataException()

    confirmation = update.message.text.lower()

    if confirmation == "no":
        update.message.reply_text(
            "Sorry that I got your question title wrong!\n"
            "Do you mind sending the name of the question here?\n"
            "Or send /cancel to cancel."
        )
        return MANUAL_NAME

    platform = context.user_data.get("PLATFORM")
    question_name = context.user_data.get("QUESTION_NAME")
    difficulty = context.user_data.get("QUESTION_DIFFICULTY")

    # Persist data to database
    user_dict = SERVICES.user_service.create_if_not_exists(
        full_name=user.full_name, telegram_id=str(user.id)
    )
    SERVICES.question_record_service.create_question_record(
        user_id=user_dict["id"],
        platform=platform,
        question_name=question_name,
        difficulty=difficulty,
    )

    SERVICES.logger.info(
        "User (%s, %s) added question: %s [%s] [%s]",
        user_dict["telegram_id"],
        user_dict["full_name"],
        question_name,
        platform,
        difficulty,
    )

    context.user_data.clear()
    update.message.reply_text(
        "Awesome! Good job with the question!", reply_markup=ReplyKeyboardRemove()
    )

    records = SERVICES.question_record_service.get_records_by_user(
        user_id=user_dict["id"], summary_type=SummaryType.WEEKLY
    )

    summary = generate_individual_summary(records, SummaryType.WEEKLY)
    update.message.reply_text(summary, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Fallback that ends the conversation and clears any cached data."""
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    if context.user_data is None:
        raise InvalidUserDataException()

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
        ],
        CONFIRM: [MessageHandler(Filters.text & ~Filters.command, confirm)],
        MANUAL_NAME: [MessageHandler(Filters.text & ~Filters.command, manual_name)],
        MANUAL_DIFFICULTY_PRE: [
            MessageHandler(Filters.regex("^(Yes|No)$"), manual_difficulty_pre)
        ],
        MANUAL_DIFFICULTY: [
            MessageHandler(Filters.regex("^(Easy|Medium|Hard)$"), manual_difficulty)
        ],
        THANKS: [
            MessageHandler(Filters.regex("^(Yes|No)$"), thanks),
            CommandHandler("cancel", cancel),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
