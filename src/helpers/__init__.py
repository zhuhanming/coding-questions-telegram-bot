from .log import logger
from .pagination import PaginationHelper
from .question import HACKERRANK_REGEX, LEETCODE_REGEX, QuestionHelper


# TODO: Look into dependency injection for this class
class AppHelper:
    def __init__(self):
        self.logger = logger
        self.question = QuestionHelper()
        self.pagination = PaginationHelper()
