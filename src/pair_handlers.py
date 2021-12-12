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
from src.utils import MONTH_ALL_SUMMARY_STRFTIME_FORMAT, unwrap

SINGLE_CONFIRM, LIST_CONFIRM = range(2)
CONFIRM_SELECTION, SWAP_COMPLETED = range(2)
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
    records: list[dict], extra_users: Optional[list[dict]]
) -> str:
    if not records:
        return "There are no interview pairings for the specified week."
    records.sort(key=lambda x: (x["is_completed"], x["user_one_name"].lower()))

    summary = f"<b>Interview Pairings for Week of {records[0]['started_at'].strftime(MONTH_ALL_SUMMARY_STRFTIME_FORMAT)}:</b>\n"
    for record in records:
        # Using .format for readability
        summary += "{} & {} [{}]\n".format(
            record["user_one_name"],
            record["user_two_name"],
            "Completed" if record["is_completed"] else "Incomplete",
        )

    if extra_users is not None:
        summary += "\nUnpaired:"
        for user in extra_users:
            summary += f"\n{user['full_name']}"

    if len(list(filter(lambda x: not x["is_completed"], records))) == 0:
        summary += "\n\nAwesome! Everyone has completed their interviews!\n"

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
    pairs = SERVICES.pair_service.get_pairs_for_chat(chat_id=chat_dict["id"])

    paired_users = set(
        [item for pair in pairs for item in [pair["user_one_id"], pair["user_two_id"]]]
    )
    new_users = set([user_dict["id"] for user_dict in user_dicts if not user_dict["is_opted_out"]]).difference(
        paired_users
    )

    new_pairs, extra_user_id = pair_users(new_users)
    if new_pairs:
        SERVICES.pair_service.add_pairs_for_chat(
            pairs=new_pairs, chat_id=chat_dict["id"]
        )
        pairs = SERVICES.pair_service.get_pairs_for_chat(chat_id=chat_dict["id"])

    summary = generate_group_interview_summary(
        pairs,
        [SERVICES.user_service.get_user_by_id(id=extra_user_id)]
        if extra_user_id is not None
        else None,
    )
    update.message.reply_html(summary)


def interview_pairs_last_week(update: Update, _: CallbackContext) -> None:
    """Lists out all pairs for mock interviews last week."""
    update.message = unwrap(update.message)
    if update.message.chat.type == "private":
        update.message.reply_text("Please use this command in a chat group!")
        return
    chat = update.message.chat
    chat_dict = SERVICES.chat_service.get_chat_by_telegram_id(telegram_id=str(chat.id))
    user_dicts = SERVICES.belong_service.get_users_in_chat(chat_id=chat_dict["id"])
    pairs = SERVICES.pair_service.get_pairs_for_chat(
        chat_id=chat_dict["id"], is_last_week=True
    )

    paired_users = set(
        [item for pair in pairs for item in [pair["user_one_id"], pair["user_two_id"]]]
    )
    unpaired_users = set([user_dict["id"] for user_dict in user_dicts]).difference(
        paired_users
    )

    summary = generate_group_interview_summary(
        pairs,
        SERVICES.user_service.get_users_by_id(ids=list(unpaired_users))
        if len(unpaired_users) > 0
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


def cancel_complete(update: Update, context: CallbackContext) -> int:
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
    fallbacks=[CommandHandler("cancel", cancel_complete)],
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


def swap_pairs(update: Update, context: CallbackContext) -> int:
    update.message = unwrap(update.message)
    if update.message.chat.type == "private":
        update.message.reply_text("Please use this command in a chat group!")
        return ConversationHandler.END
    if context.chat_data is None:
        raise InvalidUserDataException()

    chat = update.message.chat
    chat_dict = SERVICES.chat_service.get_chat_by_telegram_id(telegram_id=str(chat.id))
    users = SERVICES.belong_service.get_users_in_chat(chat_id=chat_dict["id"])
    context.chat_data["USERS_FOR_SWAPPING"] = users

    message = "Please reply to this message with two space-separated numbers, indicating the two people you would like to swap!\n\n"

    for index, user in enumerate(users):
        message += f"{index + 1}. {user['full_name']}\n"

    update.message.reply_text(message)
    return CONFIRM_SELECTION


def confirm_swap_selection(update: Update, context: CallbackContext) -> int:
    update.message = unwrap(update.message)
    update.message.text = unwrap(update.message.text)
    if context.chat_data is None:
        raise InvalidUserDataException()

    numbers = update.message.text.split(" ")
    if len(numbers) != 2 or sum([1 if x.isnumeric() else 0 for x in numbers]) != 2:
        update.message.reply_text(
            "Please reply to this message two numbers separated by a space!\nOr /cancel to stop."
        )
        return CONFIRM_SELECTION

    num_1, num_2 = [int(x) for x in numbers]
    users = context.chat_data.get("USERS_FOR_SWAPPING")
    if not 0 < num_1 <= len(users) or not 0 < num_2 <= len(users):
        update.message.reply_text(
            "Please reply to this message two valid numbers separated by a space!\nOr /cancel to stop."
        )
        return CONFIRM_SELECTION

    chat = update.message.chat
    chat_dict = SERVICES.chat_service.get_chat_by_telegram_id(telegram_id=str(chat.id))

    user_1 = users[num_1 - 1]
    user_2 = users[num_2 - 1]

    pair_list_1 = SERVICES.pair_service.get_pairs_for_user(
        user_id=user_1["id"], is_current=True
    )
    pair_list_1 = [pair for pair in pair_list_1 if pair["chat_id"] == chat_dict["id"]]
    pair_1 = None if len(pair_list_1) == 0 else pair_list_1[0]

    pair_list_2 = SERVICES.pair_service.get_pairs_for_user(
        user_id=user_2["id"], is_current=True
    )
    pair_list_2 = [pair for pair in pair_list_2 if pair["chat_id"] == chat_dict["id"]]
    pair_2 = None if len(pair_list_2) == 0 else pair_list_2[0]

    if pair_1 is None and pair_2 is None:
        update.message.reply_text(
            "Both of these users are not paired! Please use the /interview_pairs command to pair users up."
        )
        context.chat_data.clear()
        return ConversationHandler.END
    if pair_1 is not None and pair_2 is not None and pair_1["id"] == pair_2["id"]:
        update.message.reply_text(
            "These two users are already paired. Please send /swap_pairs again if you wish to swap other users."
        )
        context.chat_data.clear()
        return ConversationHandler.END
    if (pair_1 is not None and pair_1["is_completed"]) or (
        pair_2 is not None and pair_2["is_completed"]
    ):
        update.message.reply_text(
            "At least one of these two users has already completed their interview. You won't be able to swap them."
        )
        context.chat_data.clear()
        return ConversationHandler.END
    if pair_1 is not None and pair_2 is not None:
        message = "After the swap, the new pairs will be:\n"
        message += f"{pair_1['self_name']} & {pair_2['partner_name']}\n"
        message += f"{pair_2['self_name']} & {pair_1['partner_name']}\n"
    elif pair_1 is None:
        assert pair_2 is not None
        message = "After the swap, the new pair will be:\n"
        message += f"{user_1['full_name']} & {pair_2['partner_name']}\n"
        message += f"{user_2['full_name']} (Unpaired)\n"
    else:
        assert pair_1 is not None
        assert pair_2 is None
        message = "After the swap, the new pair will be:\n"
        message += f"{user_2['full_name']} & {pair_1['partner_name']}\n"
        message += f"{user_1['full_name']} (Unpaired)\n"

    context.chat_data["SWAP_DATA"] = (
        (user_1["id"], pair_1["id"] if pair_1 is not None else None),
        (user_2["id"], pair_2["id"] if pair_2 is not None else None),
    )  # ((user_one_id, pair_one_id), (user_two_id, pair_two_id))
    message += "\nIs this ok?"
    update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(CONFIRM_KEYBOARD, one_time_keyboard=True),
    )
    return SWAP_COMPLETED


def swap_completed(update: Update, context: CallbackContext) -> int:
    update.message = unwrap(update.message)
    update.message.text = unwrap(update.message.text)
    if context.chat_data is None:
        raise InvalidUserDataException()

    confirmation = update.message.text.lower()

    if confirmation == "no":
        update.message.reply_text(
            "Ok, no worries. The swap has been cancelled.",
            reply_markup=ReplyKeyboardRemove(),
        )
        context.chat_data.clear()
        return ConversationHandler.END

    swap_data = context.chat_data["SWAP_DATA"]
    user_one_id, pair_one_id = swap_data[0]
    user_two_id, pair_two_id = swap_data[1]
    SERVICES.pair_service.swap_pairs_for_users(
        user_one_id=user_one_id,
        user_two_id=user_two_id,
        pair_one_id=pair_one_id,
        pair_two_id=pair_two_id,
    )

    message = "Swap has been done!\n\n"

    chat = update.message.chat
    chat_dict = SERVICES.chat_service.get_chat_by_telegram_id(telegram_id=str(chat.id))
    user_dicts = SERVICES.belong_service.get_users_in_chat(chat_id=chat_dict["id"])
    pairs = SERVICES.pair_service.get_pairs_for_chat(chat_id=chat_dict["id"])
    paired_users = set(
        [item for pair in pairs for item in [pair["user_one_id"], pair["user_two_id"]]]
    )
    unpaired_users = set([user_dict["id"] for user_dict in user_dicts]).difference(
        paired_users
    )

    message += generate_group_interview_summary(
        pairs,
        SERVICES.user_service.get_users_by_id(ids=list(unpaired_users))
        if len(unpaired_users) > 0
        else None,
    )
    update.message.reply_html(
        message,
        reply_markup=ReplyKeyboardRemove(),
    )
    context.chat_data.clear()
    return ConversationHandler.END


def cancel_swap(update: Update, context: CallbackContext) -> int:
    """Fallback that ends the conversation and clears any cached data."""
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    if context.user_data is None:
        raise InvalidUserDataException()

    update.message.reply_text(
        "The swap has been cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )

    context.user_data.clear()
    return ConversationHandler.END


swap_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("swap_pairs", swap_pairs)],
    states={
        CONFIRM_SELECTION: [
            MessageHandler(Filters.regex("^\d+ \d+$"), confirm_swap_selection)
        ],
        SWAP_COMPLETED: [MessageHandler(Filters.regex("^(Yes|No)$"), swap_completed)],
    },
    fallbacks=[CommandHandler("cancel", cancel_swap)],
)
