from enum import Enum


class SummaryType(Enum):
    WEEKLY = "week"
    MONTHLY = "month"
    ALL = "all time"
    ALL_UNIQUE = "all time (unique)"
