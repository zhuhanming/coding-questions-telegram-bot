from re import match

from telegram import (
    InlineKeyboardButton,
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

from src.config import APP_CONFIG
from src.exceptions import InvalidUserDataException
from src.schemata import HACKERRANK_REGEX, LEETCODE_REGEX
from src.services import SERVICES
from src.stats_handlers import SummaryType, generate_individual_summary
from src.utils import reply_html, unwrap

FETCH, MANUAL_NAME, MANUAL_DIFFICULTY_PRE, MANUAL_DIFFICULTY, THANKS = range(5)
DIFFICULTY_KEYBOARD = [["Easy"], ["Medium"], ["Hard"]]
CONFIRM_KEYBOARD = [["Yes"], ["No"]]
GET_STARTED_KEYBOARD = [
    [InlineKeyboardButton(text="Get started", url=APP_CONFIG["BOT_URL"])]
]


"""
Flow for add question:
- Ask for URL.
- Try to identify the platform. If identifiable, fetch the question details.
- Otherwise, ask for the platform, question title, difficulty level.
- Confirm one more time before adding question.
"""


def add(update: Update, context: CallbackContext) -> int:
    """Kicks off the question adding process and asks user for the question URL."""
    # Unwrap and fail fast
    user = unwrap(update.effective_user)
    update.message = unwrap(update.message)

    if update.message.chat.type != "private":
        try:
            context.bot.send_message(
                chat_id=user.id, text="Please resend /add_question here again!"
            )
            update.message.reply_text("I have messaged you for this!")
        except Unauthorized:
            update.message.reply_text(
                "You need to start a conversation with me first!",
                reply_markup=InlineKeyboardMarkup(GET_STARTED_KEYBOARD),
            )
        finally:
            return ConversationHandler.END

    update.message.reply_text(
        f"Hi {user.full_name}! Glad to see that you've been working hard!\n"
        "Can you send me the URL of the question that you attempted?\n"
        "You can also send /cancel to cancel.",
    )
    return FETCH


def try_fetch_details(update: Update, context: CallbackContext) -> int:
    """Tries to identify the platform before fetching question details. If unidentifiable, will kickstart the process of getting details manually."""
    update.message = unwrap(update.message)
    update.message.text = unwrap(update.message.text)
    if context.user_data is None:
        raise InvalidUserDataException()

    url = update.message.text.lower()
    platform = "other"
    if bool(match(LEETCODE_REGEX, url)):
        platform = "leetcode"
    elif bool(match(HACKERRANK_REGEX, url)):
        platform = "hackerrank"

    context.user_data["PLATFORM"] = platform

    if platform == "other":
        update.message.reply_text(
            "I was unable to fetch the question details from your URL.\n"
            "Do you mind letting me know what the name of the question you attempted was?\n"
            "You can also send /cancel to cancel.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return MANUAL_NAME

    is_leetcode = platform == "leetcode"
    update.message.reply_text(
        "This part may take a while to load.\n" "Do be patient with me!"
    )

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
            "I tried my best to get the question title either from the website or from the URL you gave!\n"
            f"Is your question title: {question_info.name}?",
            reply_markup=ReplyKeyboardMarkup(CONFIRM_KEYBOARD, one_time_keyboard=True),
        )
        return MANUAL_DIFFICULTY_PRE

    assert question_info.name is not None
    assert question_info.difficulty is not None

    update.message.reply_text(
        "I managed to find the question info from the website directly!\n"
        f"Is your question: {question_info.name} [{question_info.difficulty.title()}]?",
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
        f"Just to confirm, is your question: {question_name} [{question_difficulty.title()}]?",
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
            "Sorry that I got your question details wrong!\n"
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
        "User %s added question: %s [%s] [%s]",
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
    reply_html(update, summary)
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
        FETCH: [MessageHandler(Filters.text & ~Filters.command, try_fetch_details)],
        MANUAL_NAME: [MessageHandler(Filters.text & ~Filters.command, manual_name)],
        MANUAL_DIFFICULTY_PRE: [
            MessageHandler(Filters.regex("^(Yes|No)$"), manual_difficulty_pre)
        ],
        MANUAL_DIFFICULTY: [
            MessageHandler(Filters.regex("^(Easy|Medium|Hard)$"), manual_difficulty)
        ],
        THANKS: [MessageHandler(Filters.regex("^(Yes|No)$"), thanks)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
