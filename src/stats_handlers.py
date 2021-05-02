from telegram import Update
from telegram.ext import CallbackContext

from src.config import APP_CONFIG
from src.services import SERVICES
from src.utils import SUMMARY_STRFTIME_FORMAT, format_platform_name, unwrap


def generate_weekly_summary(records: list[dict]) -> str:
    if not records:
        return "You have not completed any questions this week!"
    summary = "Questions you have completed this week:\n\n"
    for i, record in enumerate(records):
        summary += "{}. {} [{}] ({})\n".format(
            i + 1,
            record["question_name"],
            format_platform_name(record["platform"]),
            record["created_at"].strftime(SUMMARY_STRFTIME_FORMAT),
        )

    if len(records) >= APP_CONFIG["WEEKLY_TARGET"]:
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
    records = SERVICES.question_record_service.get_records_by_user_for_this_week(
        user_id=user_dict["id"]
    )

    summary = generate_weekly_summary(records)
    update.message.reply_text(summary)
