from enum import Enum
from typing import Optional, TypeVar

from src.exceptions import InvalidUnwrapException

WEEK_SUMMARY_STRFTIME_FORMAT = "%A"
MONTH_ALL_SUMMARY_STRFTIME_FORMAT = "%-d %b"
T = TypeVar("T")


class SummaryType(Enum):
    WEEKLY = "this week"
    MONTHLY = "this month"
    ALL = "all time"
    ALL_UNIQUE = "all time (unique)"


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
