import logging
from datetime import datetime, timedelta
from sys import stdout
from time import sleep
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from src.config import APP_CONFIG
from src.database import Belong, Chat, QuestionRecord, User, session_scope
from src.exceptions import ResourceNotFoundException
from src.schemata import (
    BELONG_SCHEMA,
    CREATE_CHAT_SCHEMA,
    CREATE_QUESTION_RECORD_SCHEMA,
    CREATE_USER_SCHEMA,
    GET_CHAT_SCHEMA,
    GET_QUESTION_RECORD_SCHEMA,
    GET_USER_SCHEMA,
    HACKERRANK_RULE,
    LEETCODE_RULE,
    UUID_RULE,
    validate_input,
)


class UserService:
    def __init__(self, config):
        self.config = config

    @validate_input(CREATE_USER_SCHEMA)
    def create_if_not_exists(self, full_name: str, telegram_id: str) -> dict:
        with session_scope() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
            if user is None:
                user = User(full_name=full_name, telegram_id=telegram_id)
                session.add(user)
                session.flush()
            else:
                user.full_name = full_name

            session.commit()
            return user.asdict()

    @validate_input(GET_USER_SCHEMA)
    def get_user_by_telegram_id(self, telegram_id: str) -> dict:
        with session_scope() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
            if user is None:
                raise ResourceNotFoundException()
            user_dict = user.asdict()
        return user_dict


class QuestionRecordService:
    def __init__(self, config):
        self.config = config

    @validate_input(CREATE_QUESTION_RECORD_SCHEMA)
    def create_question_record(
        self, user_id: str, platform: str, question_name: str
    ) -> dict:
        with session_scope() as session:
            user = session.query(User).get(user_id)
            if user is None:
                raise ResourceNotFoundException()

            question_record = QuestionRecord(
                user_id=user_id, platform=platform, question_name=question_name
            )

            session.add(question_record)
            session.commit()

            return question_record.asdict()

    @validate_input(GET_QUESTION_RECORD_SCHEMA)
    def get_all_records_by_user(self, user_id: str) -> List[dict]:
        with session_scope() as session:
            question_orders = (
                session.query(QuestionRecord)
                .filter_by(user_id=user_id)
                .order_by(QuestionRecord.created_at)
                .all()
            )
            return [question_order.asdict() for question_order in question_orders]

    @validate_input(GET_QUESTION_RECORD_SCHEMA)
    def get_records_by_user_for_this_week(self, user_id: str) -> List[dict]:
        now = datetime.now()
        monday = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        with session_scope() as session:
            question_orders = (
                session.query(QuestionRecord)
                .filter_by(user_id=user_id)
                .filter(QuestionRecord.created_at >= monday)
                .order_by(QuestionRecord.created_at)
                .all()
            )
            return [question_order.asdict() for question_order in question_orders]


class ChatService:
    def __init__(self, config):
        self.config = config

    @validate_input(CREATE_CHAT_SCHEMA)
    def create_if_not_exists(self, title: str, telegram_id: str) -> dict:
        with session_scope() as session:
            chat = session.query(Chat).filter_by(telegram_id=telegram_id).one_or_none()
            if chat is None:
                chat = Chat(title=title, telegram_id=telegram_id)
                session.add(chat)
                session.flush()
            else:
                chat.title = title

            session.commit()
            return chat.asdict()

    @validate_input(GET_CHAT_SCHEMA)
    def get_chat_by_telegram_id(self, telegram_id: str) -> dict:
        with session_scope() as session:
            chat = session.query(Chat).filter_by(telegram_id=telegram_id).one_or_none()
            if chat is None:
                raise ResourceNotFoundException()
            chat_dict = chat.asdict()
        return chat_dict


class BelongService:
    def __init__(self, config):
        self.config = config

    @validate_input(BELONG_SCHEMA)
    def add_user_to_chat_if_not_inside(self, user_id: str, chat_id: str) -> dict:
        with session_scope() as session:
            belong = (
                session.query(Belong)
                .filter_by(user_id=user_id, chat_id=chat_id)
                .one_or_none()
            )
            if belong is None:
                belong = Belong(user_id=user_id, chat_id=chat_id)
                session.add(belong)
                session.flush()
            session.commit()
            return belong.asdict()

    @validate_input(BELONG_SCHEMA)
    def remove_user_from_chat_if_inside(self, user_id: str, chat_id: str) -> dict:
        with session_scope() as session:
            belong = (
                session.query(Belong)
                .filter_by(user_id=user_id, chat_id=chat_id)
                .one_or_none()
            )
            if belong is not None:
                session.delete(belong)
        return {}

    @validate_input({"chat_id": UUID_RULE})
    def get_users_in_chat(self, chat_id: str) -> List[dict]:
        with session_scope() as session:
            users = [
                u.asdict()
                for u in session.query(User)
                .join(Belong, Belong.user_id == User.id)
                .filter(Belong.chat_id == chat_id)
                .all()
            ]
        return users

    @validate_input(BELONG_SCHEMA)
    def is_user_inside_chat(self, user_id: str, chat_id: str) -> bool:
        with session_scope() as session:
            belong = (
                session.query(Belong)
                .filter_by(user_id=user_id, chat_id=chat_id)
                .one_or_none()
            )
            return belong is not None


class QuestionNameService:
    def __init__(self, config):
        self.config = config
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(), options=chrome_options
        )

    @validate_input({"url": LEETCODE_RULE})
    def get_leetcode_question_name(self, url: str) -> Optional[str]:
        self.driver.get(url)
        sleep(0.5)
        page_name = self.driver.title

        if self.__is_invalid_leetcode_page_name(page_name):
            return None

        question_name = page_name[:-11]
        return question_name

    @validate_input({"url": LEETCODE_RULE})
    def parse_leetcode_url_directly(self, url: str) -> Optional[str]:
        split_url = url.split("/problems/")
        if len(split_url) < 2:
            return None
        problem_name_kebab = split_url[1]
        problem_name_split = problem_name_kebab.split("-")
        problem_name = " ".join(list(map(lambda x: x.title(), problem_name_split)))

        if problem_name[-1] == "/":
            problem_name = problem_name[:-1]

        return problem_name

    def __is_invalid_leetcode_page_name(self, page_name: str) -> bool:
        if not page_name:
            return True
        page_name = page_name.lower()
        invalid_strings = ["account login", "page not found"]
        for invalid_string in invalid_strings:
            if invalid_string in page_name:
                return True
        return False

    @validate_input({"url": HACKERRANK_RULE})
    def get_hackerrank_question_name(self, url: str) -> Optional[str]:
        self.driver.get(url)
        sleep(0.5)
        page_name = self.driver.title

        if self.__is_invalid_hackerrank_page_name(page_name):
            return None

        question_name = page_name[:-11]
        return question_name

    @validate_input({"url": HACKERRANK_RULE})
    def parse_hackerrank_url_directly(self, url: str) -> Optional[str]:
        split_url = url.split("/problems/")
        if len(split_url) < 2:
            return None
        problem_name_kebab = split_url[1]
        problem_name_split = problem_name_kebab.split("-")
        problem_name = " ".join(list(map(lambda x: x.title(), problem_name_split)))

        if problem_name[-1] == "/":
            problem_name = problem_name[:-1]

        return problem_name

    def __is_invalid_hackerrank_page_name(self, page_name: str) -> bool:
        if not page_name:
            return True
        page_name = page_name.lower()
        invalid_strings = ["account login", "page not found"]
        for invalid_string in invalid_strings:
            if invalid_string in page_name:
                return True
        return False


class Services:
    pass


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

stdout_handler = logging.StreamHandler(stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.addFilter(lambda record: record.levelno == logging.INFO)
stderr_handler = logging.StreamHandler()
stderr_handler.setLevel(logging.WARNING)

logger.addHandler(stdout_handler)
logger.addHandler(stderr_handler)

SERVICES = Services()
SERVICES.config = APP_CONFIG
SERVICES.user_service = UserService(SERVICES.config)
SERVICES.chat_service = ChatService(SERVICES.config)
SERVICES.belong_service = BelongService(SERVICES.config)
SERVICES.question_record_service = QuestionRecordService(SERVICES.config)
SERVICES.question_name_service = QuestionNameService(SERVICES.config)
SERVICES.logger = logger
