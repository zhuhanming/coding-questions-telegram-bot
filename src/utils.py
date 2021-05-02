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
