from typing import TypeVar

from .exceptions import InvalidUnwrapException

T = TypeVar("T")


def unwrap(optional: T | None) -> T:
    if optional is None:
        raise InvalidUnwrapException()
    return optional
