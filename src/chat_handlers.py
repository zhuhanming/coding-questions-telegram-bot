from telegram import Update
from telegram.ext import CallbackContext

from src.exceptions import ResourceNotFoundException
from src.services import SERVICES
from src.utils import generate_user_list


def new_chat_member_handler(update: Update, _: CallbackContext) -> None:
    new_users = update.message.new_chat_members
    added_new_users = []
    for user in new_users:
        if user.is_bot:
            continue
        user = SERVICES.user_service.create_if_not_exists(
            full_name=user.full_name, telegram_id=str(user.id)
        )
        added_new_users.append(user)

    chat = update.message.chat
    chat = SERVICES.chat_service.create_if_not_exists(
        title=chat.title, telegram_id=str(chat.id)
    )
    for user in added_new_users:
        SERVICES.belong_service.add_user_to_chat_if_not_inside(
            user_id=user["id"], chat_id=chat["id"]
        )
        SERVICES.logger.info(
            "Added {} to chat {}".format(user["full_name"], chat["title"])
        )


def left_chat_member_handler(update: Update, _: CallbackContext) -> None:
    user = update.message.left_chat_member
    try:
        user = SERVICES.user_service.get_user_by_telegram_id(telegram_id=str(user.id))
        chat = update.message.chat
        chat = SERVICES.chat_service.get_chat_by_telegram_id(telegram_id=str(chat.id))
        SERVICES.belong_service.remove_user_from_chat_if_inside(
            user_id=user["id"], chat_id=chat["id"]
        )
        SERVICES.logger.info(
            "Removed {} from chat {}".format(user["full_name"], chat["title"])
        )
    except ResourceNotFoundException:
        return


def chat_members(update: Update, _: CallbackContext) -> None:
    chat = update.message.chat
    if chat.type == "private":
        update.message.reply_text("I'm only talking to you here!")
        return
    chat = SERVICES.chat_service.get_chat_by_telegram_id(telegram_id=str(chat.id))
    users = SERVICES.belong_service.get_users_in_chat(chat_id=chat["id"])

    message = generate_user_list(chat, users)
    update.message.reply_text(message)


def add_me(update: Update, _: CallbackContext) -> None:
    chat = update.message.chat
    if chat.type == "private":
        update.message.reply_text("Please use this command in a chat group!")
        return

    chat = SERVICES.chat_service.create_if_not_exists(
        title=chat.title, telegram_id=str(chat.id)
    )
    user = update.effective_user
    user = SERVICES.user_service.create_if_not_exists(
        full_name=user.full_name, telegram_id=str(user.id)
    )

    if SERVICES.belong_service.is_user_inside_chat(
        user_id=user["id"], chat_id=chat["id"]
    ):
        update.message.reply_text("You're already inside this chat group!")
    else:
        SERVICES.belong_service.add_user_to_chat_if_not_inside(
            user_id=user["id"], chat_id=chat["id"]
        )
        SERVICES.logger.info(
            "Added {} to chat {}".format(user["full_name"], chat["title"])
        )
        update.message.reply_text("Added you to this chat group!")

    users = SERVICES.belong_service.get_users_in_chat(chat_id=chat["id"])
    message = generate_user_list(chat, users)
    update.message.reply_text(message)
