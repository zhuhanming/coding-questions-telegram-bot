from typing import Optional, TypeVar

from src.exceptions import InvalidUnwrapException

SUMMARY_STRFTIME_FORMAT = "%A"
T = TypeVar("T")


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
