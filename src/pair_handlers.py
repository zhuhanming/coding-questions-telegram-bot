from random import shuffle
from typing import Optional

from telegram import Update
from telegram.ext import CallbackContext

from src.services import SERVICES
from src.utils import MONTH_ALL_SUMMARY_STRFTIME_FORMAT, get_start_of_week, unwrap


def pair_users(user_ids: set[str]) -> tuple[list[list[str]], Optional[str]]:
    user_id_list = list(user_ids)
    shuffle(user_id_list)
    pairs = []

    for i in range(1, len(user_id_list), 2):
        pairs.append([user_id_list[i - 1], user_id_list[i]])

    return (pairs, None if len(user_id_list) % 2 == 0 else user_id_list[-1])


def generate_group_interview_summary(
    records: list[dict], extra_user: Optional[dict]
) -> str:
    if not records:
        return "This group has no members! Add yourself using /add_me now."
    records.sort(
        key=lambda x: (x["pair"]["is_completed"], len(x["user_one"]["full_name"]))
    )

    summary = "<b>Interview Pairings for Week of {}:</b>\n".format(
        get_start_of_week().strftime(MONTH_ALL_SUMMARY_STRFTIME_FORMAT)
    )
    for record in records:
        summary += "{} & {}: {}\n".format(
            record["user_one"]["full_name"],
            record["user_two"]["full_name"],
            "Completed" if record["pair"]["is_completed"] else "Incomplete",
        )

    if extra_user is not None:
        summary += "\nUnpaired: {}\n".format(extra_user["full_name"])

    if len(list(filter(lambda x: not x["pair"]["is_completed"], records))) == 0:
        summary += "\nAwesome! Everyone has completed their interviews!\n"

    return summary


def interview_pairs(update: Update, _: CallbackContext) -> None:
    update.message = unwrap(update.message)
    if update.message.chat.type != "group":
        update.message.reply_text("Please use this command in a chat group!")
        return
    chat = update.message.chat
    chat_dict = SERVICES.chat_service.get_chat_by_telegram_id(telegram_id=str(chat.id))
    user_dicts = SERVICES.belong_service.get_users_in_chat(chat_id=chat_dict["id"])
    pairs = SERVICES.pair_service.get_current_pairs_for_chat(chat_id=chat_dict["id"])

    paired_users = set(
        [pair["user_one"]["id"] for pair in pairs]
        + [pair["user_two"]["id"] for pair in pairs]
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
