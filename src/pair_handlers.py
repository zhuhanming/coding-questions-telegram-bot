from random import shuffle
from typing import Optional

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
from src.services import SERVICES
from src.utils import MONTH_ALL_SUMMARY_STRFTIME_FORMAT, get_start_of_week, unwrap

SINGLE_CONFIRM, LIST_CONFIRM = range(2)
CONFIRM_KEYBOARD = [["Yes"], ["No"]]
GET_STARTED_KEYBOARD = [
    [InlineKeyboardButton(text="Get started", url=APP_CONFIG["BOT_URL"])]
]

# Helpers


def pair_users(user_ids: set[str]) -> tuple[list[list[str]], Optional[str]]:
    user_id_list = list(user_ids)
    shuffle(user_id_list)
    pairs = []

    for i in range(1, len(user_id_list), 2):
        pairs.append([user_id_list[i - 1], user_id_list[i]])

    return (pairs, None if len(user_id_list) % 2 == 0 else user_id_list[-1])


def notify_partner(context: CallbackContext, pair: dict):
    partner_dict = SERVICES.user_service.get_user_by_id(id=pair["partner_id"])
    try:
        context.bot.send_message(
            chat_id=partner_dict["telegram_id"],
            # Using .format for readability
            text="Your mock interview with {} [{}] has been marked as completed by them!".format(
                pair["self_name"], pair["chat_title"]
            ),
        )
    except Unauthorized:
        SERVICES.logger.info(
            f"Could not notify partner: {pair['partner_name']} [{pair['chat_title']}]",
        )


# Summary Generators


def generate_individual_interview_summary(records: list[dict]) -> str:
    if not records:
        return (
            "You have no mock interviews arranged!\n"
            "Join a group with this bot and use the /interview_pairs command to get started!"
        )

    summary = "<b>All Past Interview Pairings:</b>\n"

    for i, record in enumerate(records):
        # Using .format for readability
        summary += "{}. {} [{}] [{}] ({})\n".format(
            i + 1,
            record["partner_name"],
            record["chat_title"],
            record["started_at"].strftime(MONTH_ALL_SUMMARY_STRFTIME_FORMAT),
            "Completed" if record["is_completed"] else "Incomplete",
        )

    return summary


def generate_group_interview_summary(
    records: list[dict], extra_user: Optional[dict]
) -> str:
    if not records:
        return "This group has no members! Add yourself using /add_me now."
    records.sort(key=lambda x: (x["is_completed"], x["user_one_name"].lower()))

    summary = f"<b>Interview Pairings for Week of {get_start_of_week().strftime(MONTH_ALL_SUMMARY_STRFTIME_FORMAT)}:</b>\n"
    for record in records:
        # Using .format for readability
        summary += "{} & {} [{}]\n".format(
            record["user_one_name"],
            record["user_two_name"],
            "Completed" if record["is_completed"] else "Incomplete",
        )

    if extra_user is not None:
        summary += f"\nUnpaired: {extra_user['full_name']}\n"

    if len(list(filter(lambda x: not x["is_completed"], records))) == 0:
        summary += "\nAwesome! Everyone has completed their interviews!\n"

    return summary


# Handlers


def interview_pairs(update: Update, _: CallbackContext) -> None:
    """Generates pairs for the group for members who have yet to be paired, and lists all pairs out."""
    update.message = unwrap(update.message)
    if update.message.chat.type == "private":
        update.message.reply_text("Please use this command in a chat group!")
        return
    chat = update.message.chat
    chat_dict = SERVICES.chat_service.get_chat_by_telegram_id(telegram_id=str(chat.id))
    user_dicts = SERVICES.belong_service.get_users_in_chat(chat_id=chat_dict["id"])
    pairs = SERVICES.pair_service.get_current_pairs_for_chat(chat_id=chat_dict["id"])

    paired_users = set(
        [item for pair in pairs for item in [pair["user_one_id"], pair["user_two_id"]]]
    )
    new_users = set([user_dict["id"] for user_dict in user_dicts]).difference(
        paired_users
    )

    new_pairs, extra_user_id = pair_users(new_users)
    if new_pairs:
        SERVICES.pair_service.add_pairs_for_chat(
            pairs=new_pairs, chat_id=chat_dict["id"]
        )
        pairs = SERVICES.pair_service.get_current_pairs_for_chat(
            chat_id=chat_dict["id"]
        )

    summary = generate_group_interview_summary(
        pairs,
        SERVICES.user_service.get_user_by_id(id=extra_user_id)
        if extra_user_id is not None
        else None,
    )
    update.message.reply_html(summary)


def complete_interview(update: Update, context: CallbackContext) -> int:
    # Unwrap and fail fast
    user = unwrap(update.effective_user)
    update.message = unwrap(update.message)
    if context.user_data is None:
        raise InvalidUserDataException()

    if update.message.chat.type != "private":
        try:
            context.bot.send_message(
                chat_id=user.id, text="Please resend /complete_interview here again!"
            )
            update.message.reply_text("I have messaged you for this!")
        except Unauthorized:
            update.message.reply_text(
                "You need to start a conversation with me first!",
                reply_markup=InlineKeyboardMarkup(GET_STARTED_KEYBOARD),
            )
        finally:
            return ConversationHandler.END

    user_dict = SERVICES.user_service.get_user_by_telegram_id(telegram_id=str(user.id))
    pairs = SERVICES.pair_service.get_pairs_for_user(user_id=user_dict["id"])

    if len(pairs) == 0:
        update.message.reply_text(
            "You have no mock interview partners arranged through me for this week!\n"
            "To get paired, please use /interview_pairs in a chat group first."
        )
        return ConversationHandler.END

    incomplete_pairs = list(filter(lambda x: not x["is_completed"], pairs))
    context.user_data["INCOMPLETE_PAIRS"] = incomplete_pairs

    if len(incomplete_pairs) == 0:
        update.message.reply_text(
            "It seems like you've completed all your mock interviews this week!\n"
            "It may have been your partner who marked this interview as completed.\n"
            "You can use the /past_pairs command to view all mock interviews you've arranged through me."
        )
        return ConversationHandler.END

    if len(incomplete_pairs) == 1:
        update.message.reply_text(
            # Using .format for readability
            "Can I confirm that you've completed your mock interview with {}, as part of the {} group?\n".format(
                incomplete_pairs[0]["partner_name"],
                incomplete_pairs[0]["chat_title"],
            )
            + "You can also send /cancel to cancel.",
            reply_markup=ReplyKeyboardMarkup(CONFIRM_KEYBOARD, one_time_keyboard=True),
        )
        return SINGLE_CONFIRM

    keyboard = [
        [f"{i + 1}. {pair['partner_name']} [{pair['chat_title']}]"]
        for i, pair in enumerate(incomplete_pairs)
    ]
    update.message.reply_text(
        "You have multiple mock interviews arranged via me for this week!\n"
        "Here's a list of mock interviews that you have yet to complete this week.\n"
        "Which one did you complete?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
    )
    return LIST_CONFIRM


def single_confirm(update: Update, context: CallbackContext) -> int:
    update.message = unwrap(update.message)
    update.message.text = unwrap(update.message.text)
    if context.user_data is None:
        raise InvalidUserDataException()

    confirmation = update.message.text.lower()

    if confirmation == "no":
        update.message.reply_text(
            "I see, no worries! All the best for the mock interview!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    pairs = context.user_data.get("INCOMPLETE_PAIRS")
    assert isinstance(pairs, list) and len(pairs) == 1
    SERVICES.pair_service.mark_pair_as_completed(id=pairs[0]["id"])
    update.message.reply_text(
        "Awesome! I have marked it as completed.", reply_markup=ReplyKeyboardRemove()
    )
    SERVICES.logger.info(
        "%s and %s [%s] have completed their mock interview",
        pairs[0]["self_name"],
        pairs[0]["partner_name"],
        pairs[0]["chat_title"],
    )
    notify_partner(context, pairs[0])

    return ConversationHandler.END


def list_confirm(update: Update, context: CallbackContext) -> int:
    update.message = unwrap(update.message)
    update.message.text = unwrap(update.message.text)
    if context.user_data is None:
        raise InvalidUserDataException()

    selected_option = update.message.text
    index, rest = selected_option.split(". ", 1)
    pairs = context.user_data.get("INCOMPLETE_PAIRS")
    assert isinstance(pairs, list) and len(pairs) > 1

    selected_pair = pairs[int(index) - 1]
    assert rest == f"{selected_pair['partner_name']} [{selected_pair['chat_title']}]"

    SERVICES.pair_service.mark_pair_as_completed(id=selected_pair["id"])
    update.message.reply_text(
        "Awesome! I have marked it as completed.", reply_markup=ReplyKeyboardRemove()
    )
    SERVICES.logger.info(
        f"{selected_pair['self_name']} and {selected_pair['partner_name']} [{selected_pair['chat_title']}] have completed their mock interview"
    )
    notify_partner(context, selected_pair)

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Fallback that ends the conversation and clears any cached data."""
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    if context.user_data is None:
        raise InvalidUserDataException()

    update.message.reply_text(
        "No worries! All the best for your mock interview!",
        reply_markup=ReplyKeyboardRemove(),
    )

    context.user_data.clear()
    return ConversationHandler.END


complete_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("complete_interview", complete_interview)],
    states={
        SINGLE_CONFIRM: [MessageHandler(Filters.regex("^(Yes|No)$"), single_confirm)],
        LIST_CONFIRM: [MessageHandler(Filters.text & ~Filters.command, list_confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


def past_pairs(update: Update, context: CallbackContext) -> None:
    # Unwrap and fail fast
    user = unwrap(update.effective_user)
    update.message = unwrap(update.message)

    if update.message.chat.type != "private":
        try:
            context.bot.send_message(
                chat_id=user.id, text="Please resend /past_pairs here again!"
            )
            update.message.reply_text("I have messaged you for this!")
        except Unauthorized:
            update.message.reply_text(
                "You need to start a conversation with me first!",
                reply_markup=InlineKeyboardMarkup(GET_STARTED_KEYBOARD),
            )
        finally:
            return

    user_dict = SERVICES.user_service.get_user_by_telegram_id(telegram_id=str(user.id))
    pairs = SERVICES.pair_service.get_pairs_for_user(
        user_id=user_dict["id"], is_current=False
    )

    summary = generate_individual_interview_summary(pairs)
    update.message.reply_html(summary)
