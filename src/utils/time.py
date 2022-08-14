from datetime import datetime, timedelta

import pytz

TIMEZONE = tz = pytz.timezone("Asia/Singapore")
WEEK_SUMMARY_STRFTIME_FORMAT = "%A"
MONTH_ALL_SUMMARY_STRFTIME_FORMAT = "%-d %b"


def get_start_of_week() -> datetime:
    now = datetime.now(tz=TIMEZONE)
    return (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def get_start_of_last_week() -> datetime:
    now = datetime.now(tz=TIMEZONE)
    return (now - timedelta(days=now.weekday() + 7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def get_start_of_month() -> datetime:
    now = datetime.now(tz=TIMEZONE)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
