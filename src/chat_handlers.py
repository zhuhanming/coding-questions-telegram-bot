from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from src.exceptions import ResourceNotFoundException
from src.services import SERVICES
from src.utils import unwrap


def generate_user_list(chat: dict, users: list[dict]) -> str:
    if not users:
        return "There are no members in this chat!\nPlease add yourself with the /add_me command."

    message = "<b>Members in {}:</b>\n".format(chat["title"])
    for user in users:
        message += "{}\n".format(user["full_name"])
    message += (
        "\nIf you're not in the list, please add yourself with the /add_me command."
    )
    return message


def new_chat_member_handler(update: Update, _: CallbackContext) -> None:
    """Adds all new non-bot users to the current chat group."""
    if update.message is None:
        # Fail silently
        return

    new_users = update.message.new_chat_members
    added_new_users = []
    for user in new_users:
        if user.username == "CodingQuestionsBot":
            update.message.reply_text(
                "You've just added the Coding Question Bot! Use /add_me to join the tracking for this chat!"
            )

        if user.is_bot:
            continue
        user = SERVICES.user_service.create_if_not_exists(
            full_name=user.full_name, telegram_id=str(user.id)
        )
        added_new_users.append(user)

    chat = update.message.chat
    chat_dict = SERVICES.chat_service.create_if_not_exists(
        title=chat.title, telegram_id=str(chat.id)
    )
    for user_dict in added_new_users:
        SERVICES.belong_service.add_user_to_chat_if_not_inside(
            user_id=user_dict["id"], chat_id=chat_dict["id"]
        )
        SERVICES.logger.info(
            "Added {} to chat {}".format(user_dict["full_name"], chat_dict["title"])
        )


def left_chat_member_handler(update: Update, _: CallbackContext) -> None:
    """Removes all non-bot users who left from the current chat group."""
    if update.message is None or update.message.left_chat_member is None:
        # Fail silently
        return

    user = update.message.left_chat_member
    chat = update.message.chat
    try:
        user_dict = SERVICES.user_service.get_user_by_telegram_id(
            telegram_id=str(user.id)
        )
        chat_dict = SERVICES.chat_service.get_chat_by_telegram_id(
            telegram_id=str(chat.id)
        )
        SERVICES.belong_service.remove_user_from_chat_if_inside(
            user_id=user_dict["id"], chat_id=chat_dict["id"]
        )
        SERVICES.logger.info(
            "Removed {} from chat {}".format(user_dict["full_name"], chat_dict["title"])
        )
    except ResourceNotFoundException:
        # User did not exist in the group. Fail silently.
        return


def chat_members(update: Update, _: CallbackContext) -> None:
    # Unwrap and fail fast
    update.message = unwrap(update.message)

    chat = update.message.chat
    if chat.type == "private":
        update.message.reply_text("I'm only talking to you here!")
        return
    chat_dict = SERVICES.chat_service.get_chat_by_telegram_id(telegram_id=str(chat.id))
    user_dicts = SERVICES.belong_service.get_users_in_chat(chat_id=chat_dict["id"])

    message = generate_user_list(chat_dict, user_dicts)
    update.message.reply_text(message, parse_mode=ParseMode.HTML)


def add_me(update: Update, _: CallbackContext) -> None:
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    user = unwrap(update.effective_user)

    chat = update.message.chat
    if chat.type == "private":
        update.message.reply_text("Please use this command in a chat group!")
        return

    chat_dict = SERVICES.chat_service.create_if_not_exists(
        title=chat.title, telegram_id=str(chat.id)
    )
    user_dict = SERVICES.user_service.create_if_not_exists(
        full_name=user.full_name, telegram_id=str(user.id)
    )

    if SERVICES.belong_service.is_user_inside_chat(
        user_id=user_dict["id"], chat_id=chat_dict["id"]
    ):
        update.message.reply_text("You're already inside this chat group!")
    else:
        SERVICES.belong_service.add_user_to_chat_if_not_inside(
            user_id=user_dict["id"], chat_id=chat_dict["id"]
        )
        SERVICES.logger.info(
            "Added {} to chat {}".format(user_dict["full_name"], chat_dict["title"])
        )
        update.message.reply_text("Added you to this chat group!")

    user_dicts = SERVICES.belong_service.get_users_in_chat(chat_id=chat_dict["id"])
    message = generate_user_list(chat_dict, user_dicts)
    update.message.reply_text(message, parse_mode=ParseMode.HTML)
