from typing import TypeVar

from src.utils.exceptions import InvalidUnwrapException

T = TypeVar("T")


def unwrap(optional: T | None) -> T:
    if optional is None:
        raise InvalidUnwrapException()
    return optional
