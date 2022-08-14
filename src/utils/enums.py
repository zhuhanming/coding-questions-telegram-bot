from enum import Enum


class SummaryType(Enum):
    WEEKLY = "week"
    MONTHLY = "month"
    ALL = "all time"
    ALL_UNIQUE = "all time (unique)"

    def format(self, is_last_week: bool = False) -> str:
        if self.name in ["WEEKLY", "MONTHLY"]:
            return ("last " if is_last_week else "this ") + self.value
        return self.value


class OptInOutType(Enum):
    QUESTIONS = "questions"
    INTERVIEWS = "interviews"
