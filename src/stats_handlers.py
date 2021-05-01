from telegram import Update
from telegram.ext import CallbackContext

from src.services import SERVICES
from src.utils import generate_weekly_summary


def week(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    if user is None or update.message is None:
        return
    user_dict = SERVICES.user_service.create_if_not_exists(
        full_name=user.full_name, telegram_id=str(user.id)
    )
    records = SERVICES.question_record_service.get_records_by_user_for_this_week(
        user_id=user_dict["id"]
    )

    summary = generate_weekly_summary(records)
    update.message.reply_text(summary)
