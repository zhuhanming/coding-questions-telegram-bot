from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from src.config import APP_CONFIG
from src.services import SERVICES
from src.utils import (
    MONTH_ALL_SUMMARY_STRFTIME_FORMAT,
    WEEK_SUMMARY_STRFTIME_FORMAT,
    SummaryType,
    format_platform_name,
    unwrap,
)


def generate_individual_summary(records: list[dict], summary_type: SummaryType) -> str:
    if not records:
        return "You have not completed any questions!"
    strftime_format = MONTH_ALL_SUMMARY_STRFTIME_FORMAT

    if summary_type == SummaryType.WEEKLY:
        strftime_format = WEEK_SUMMARY_STRFTIME_FORMAT

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


def week(update: Update, _: CallbackContext) -> None:
    update.message = unwrap(update.message)
    user = update.effective_user
    # TODO: Add handling for /week in chats
    if user is None:
        return
    user_dict = SERVICES.user_service.create_if_not_exists(
        full_name=user.full_name, telegram_id=str(user.id)
    )
    records = SERVICES.question_record_service.get_records_by_user(
        user_id=user_dict["id"], summary_type=SummaryType.WEEKLY
    )

    summary = generate_individual_summary(records, SummaryType.WEEKLY)
    update.message.reply_text(summary, parse_mode=ParseMode.HTML)


def month(update: Update, _: CallbackContext) -> None:
    update.message = unwrap(update.message)
    user = update.effective_user
    # TODO: Add handling for /month in chats
    if user is None:
        return
    user_dict = SERVICES.user_service.create_if_not_exists(
        full_name=user.full_name, telegram_id=str(user.id)
    )
    records = SERVICES.question_record_service.get_records_by_user(
        user_id=user_dict["id"], summary_type=SummaryType.WEEKLY
    )

    summary = generate_individual_summary(records, SummaryType.MONTHLY)
    update.message.reply_text(summary, parse_mode=ParseMode.HTML)


def all_questions(update: Update, _: CallbackContext) -> None:
    update.message = unwrap(update.message)
    user = update.effective_user
    # TODO: Add handling for /month in chats
    if user is None:
        return
    user_dict = SERVICES.user_service.create_if_not_exists(
        full_name=user.full_name, telegram_id=str(user.id)
    )
    records = SERVICES.question_record_service.get_records_by_user(
        user_id=user_dict["id"], summary_type=SummaryType.ALL
    )

    summary = generate_individual_summary(records, SummaryType.ALL)
    update.message.reply_text(summary, parse_mode=ParseMode.HTML)


def all_unique(update: Update, _: CallbackContext) -> None:
    update.message = unwrap(update.message)
    user = update.effective_user
    # TODO: Add handling for /month in chats
    if user is None:
        return
    user_dict = SERVICES.user_service.create_if_not_exists(
        full_name=user.full_name, telegram_id=str(user.id)
    )
    records = SERVICES.question_record_service.get_records_by_user(
        user_id=user_dict["id"], summary_type=SummaryType.ALL_UNIQUE
    )

    summary = generate_individual_summary(records, SummaryType.ALL_UNIQUE)
    update.message.reply_text(summary, parse_mode=ParseMode.HTML)
