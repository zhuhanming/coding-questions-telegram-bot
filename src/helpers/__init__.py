from .log import logger
from .question import HACKERRANK_REGEX, LEETCODE_REGEX, QuestionHelper


# TODO: Look into dependency injection for this class
class AppHelper:
    def __init__(self):
        self.logger = logger
        self.question = QuestionHelper()
