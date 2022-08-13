from .log import logger
from .question import QuestionHelper


class AppHelper:
    def __init__(self):
        self.logger = logger
        self.question = QuestionHelper()


APP_HELPER = AppHelper()
