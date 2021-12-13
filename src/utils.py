from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, TypeVar

from telegram.update import Update

from src.exceptions import InvalidUnwrapException

WEEK_SUMMARY_STRFTIME_FORMAT = "%A"
MONTH_ALL_SUMMARY_STRFTIME_FORMAT = "%-d %b"
T = TypeVar("T")
MAX_MESSAGE_LENGTH = 4000


class SummaryType(Enum):
    WEEKLY = "week"
    MONTHLY = "month"
    ALL = "all time"
    ALL_UNIQUE = "all time (unique)"

    def format(self, is_last_week: bool = False) -> str:
        if self.name in ["WEEKLY", "MONTHLY"]:
            return ("last " if is_last_week else "this ") + self.value
        return self.value


class QuestionInfo:
    def __init__(self, name: Optional[str], difficulty: Optional[str]):
        self.name = name
        self.difficulty = difficulty


def unwrap(optional: Optional[T]) -> T:
    if optional is None:
        raise InvalidUnwrapException()
    return optional


def format_platform_name(name: str) -> str:
    if name.lower() == "leetcode":
        return "LeetCode"
    if name.lower() == "hackerrank":
        return "HackerRank"
    return "Other"


def difficulty_to_int(difficulty: str) -> int:
    if difficulty.lower() == "easy":
        return 0
    if difficulty.lower() == "medium":
        return 1
    return 2


def platform_to_int(platform: str) -> int:
    if platform.lower() == "leetcode":
        return 0
    if platform.lower() == "hackerrank":
        return 1
    return 2


def get_start_of_week() -> datetime:
    now = datetime.now()
    return (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def get_start_of_last_week() -> datetime:
    now = datetime.now()
    return (now - timedelta(days=now.weekday() + 7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def get_start_of_month() -> datetime:
    now = datetime.now()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


# Desired behaviour:
# - If the new line is longer than the max message length, we break it up
#   and append the first part to the existing content.
# - Else if the existing content + new line exceeds the max message length,
#   the new line goes on to the next message.
# - Else we just append the new line to the existing content.
def break_message_up(message: str) -> list[str]:
    lines = message.split("\n")
    messages_to_send: list[str] = []

    current_lines: list[str] = []
    current_length = 0

    # We may need to push lines back into the "stack" of lines, so we will
    # use a while loop here.
    while lines:
        line = lines.pop(0).strip()
        if len(line) > MAX_MESSAGE_LENGTH:
            words = line.split(" ")
            current_words: list[str] = []
            while words:
                word = words.pop(0)
                # +1 to overcompensate for the space
                if current_length + len(word) + 1 <= MAX_MESSAGE_LENGTH:
                    current_length += len(word) + 1
                    current_words.append(word)
                else:
                    # Reinsert back into the word stack
                    words.insert(0, word)

                    current_lines.append(" ".join(current_words))
                    messages_to_send.append("\n".join(current_lines))

                    # Reinsert back into the lines stack
                    lines.insert(0, " ".join(words))

                    # Reset
                    current_words = []
                    current_lines = []
                    current_length = 0
                    break
            # Means somehow all words were consumed w/o exceeding
            if current_words:
                assert len(words) == 0
                current_lines.append(" ".join(current_words))
                messages_to_send.append("\n".join(current_lines))
                current_lines = []
                current_length = 0
        elif current_length + len(line) + 1 > MAX_MESSAGE_LENGTH:
            messages_to_send.append("\n".join(current_lines))
            current_lines = [line]
            current_length = len(line) + 1
        else:
            current_lines.append(line)
            current_length += len(line) + 1

    if current_lines:
        messages_to_send.append("\n".join(current_lines))

    return messages_to_send


def reply_html(update: Update, message: str, **kwargs) -> None:
    # Unwrap and fail fast
    update.message = unwrap(update.message)
    messages_to_send = break_message_up(message)

    for message in messages_to_send:
        update.message.reply_html(message, **kwargs)
