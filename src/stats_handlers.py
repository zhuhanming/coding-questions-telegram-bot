from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from src.config import APP_CONFIG
from src.services import SERVICES
from src.utils import (
    MONTH_ALL_SUMMARY_STRFTIME_FORMAT,
    WEEK_SUMMARY_STRFTIME_FORMAT,
    SummaryType,
    difficulty_to_int,
    format_platform_name,
    platform_to_int,
    unwrap,
)

# Summary Generators


def generate_individual_summary(records: list[dict], summary_type: SummaryType) -> str:
    if not records:
        return "You have not completed any questions!"
    strftime_format = MONTH_ALL_SUMMARY_STRFTIME_FORMAT

    if summary_type == SummaryType.WEEKLY:
        strftime_format = WEEK_SUMMARY_STRFTIME_FORMAT
    if summary_type == SummaryType.ALL_UNIQUE:
        records.sort(
            key=lambda x: (
                difficulty_to_int(x["difficulty"]),
                platform_to_int(x["platform"]),
            )
        )

    summary = "<b>Questions you have completed {}:</b>\n".format(summary_type.value)
    for i, record in enumerate(records):
        if summary_type == SummaryType.ALL_UNIQUE:
            summary += "{}. {} [{}] [{}]\n".format(
                i + 1,
                record["question_name"],
                record["difficulty"].title(),
                format_platform_name(record["platform"]),
            )
            continue

        summary += "{}. {} [{}] [{}] ({})\n".format(
            i + 1,
            record["question_name"],
            record["difficulty"].title(),
            format_platform_name(record["platform"]),
            record["created_at"].strftime(strftime_format),
        )

    if (
        summary_type == SummaryType.WEEKLY
        and len(records) >= APP_CONFIG["WEEKLY_TARGET"]
    ):
        summary += "\nAwesome! You have achieved the weekly target!\n"

    return summary


def generate_group_summary(records: dict[str, dict], summary_type: SummaryType) -> str:
    if not records:
        return "This group has no members! Add yourself using /add_me now."
    record_list = list(records.values())
    record_list.sort(key=lambda x: len(x["question_records"]), reverse=True)

    summary = "<b>Questions completed {}:</b>\n".format(summary_type.value)
    for record in record_list:
        summary += "{}: {} completed\n".format(
            record["full_name"], len(record["question_records"])
        )

    if (
        summary_type == SummaryType.WEEKLY
        and min(map(lambda x: len(x["question_records"]), record_list))
        >= APP_CONFIG["WEEKLY_TARGET"]
    ):
        summary += "\nAwesome! Everyone has achieved the weekly target!\n"

    return summary


# Summary Helpers


def create_and_send_individual_summary(
    update: Update, summary_type: SummaryType
) -> None:
    update.message = unwrap(update.message)
    user = unwrap(update.effective_user)

    user_dict = SERVICES.user_service.create_if_not_exists(
        full_name=user.full_name, telegram_id=str(user.id)
    )
    records = SERVICES.question_record_service.get_records_by_user(
        user_id=user_dict["id"], summary_type=summary_type
    )

    summary = generate_individual_summary(records, summary_type)
    update.message.reply_text(summary, parse_mode=ParseMode.HTML)


def create_and_send_group_summary(update: Update, summary_type: SummaryType) -> None:
    update.message = unwrap(update.message)
    chat = update.message.chat
    chat_dict = SERVICES.chat_service.get_chat_by_telegram_id(telegram_id=str(chat.id))
    user_dicts = SERVICES.belong_service.get_users_in_chat(chat_id=chat_dict["id"])
    records = SERVICES.question_record_service.get_records_by_users(
        user_ids=[user_dict["id"] for user_dict in user_dicts],
        summary_type=summary_type,
    )

    summary = generate_group_summary(records, summary_type)
    update.message.reply_text(summary, parse_mode=ParseMode.HTML)


# Individual Handlers


def week(update: Update, context: CallbackContext) -> None:
    update.message = unwrap(update.message)
    if update.message.chat.type == "group":
        week_chat(update, context)
        return
    create_and_send_individual_summary(update, SummaryType.WEEKLY)


def month(update: Update, context: CallbackContext) -> None:
    update.message = unwrap(update.message)
    if update.message.chat.type == "group":
        month_chat(update, context)
        return
    create_and_send_individual_summary(update, SummaryType.MONTHLY)


def all_questions(update: Update, context: CallbackContext) -> None:
    update.message = unwrap(update.message)
    if update.message.chat.type == "group":
        all_questions_chat(update, context)
        return
    create_and_send_individual_summary(update, SummaryType.ALL)


def all_unique(update: Update, context: CallbackContext) -> None:
    update.message = unwrap(update.message)
    if update.message.chat.type == "group":
        all_unique_chat(update, context)
        return
    create_and_send_individual_summary(update, SummaryType.ALL_UNIQUE)


# Group Handlers


def week_chat(update: Update, _: CallbackContext) -> None:
    create_and_send_group_summary(update, SummaryType.WEEKLY)


def month_chat(update: Update, _: CallbackContext) -> None:
    create_and_send_group_summary(update, SummaryType.MONTHLY)


def all_questions_chat(update: Update, _: CallbackContext) -> None:
    create_and_send_group_summary(update, SummaryType.ALL)


def all_unique_chat(update: Update, _: CallbackContext) -> None:
    create_and_send_group_summary(update, SummaryType.ALL_UNIQUE)
