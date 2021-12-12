import logging
from datetime import datetime
from sys import stdout
from time import sleep
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import or_
from webdriver_manager.chrome import ChromeDriverManager

from src.config import APP_CONFIG, Config
from src.database import (
    Belong,
    Chat,
    InterviewPair,
    QuestionRecord,
    User,
    session_scope,
)
from src.exceptions import ResourceNotFoundException
from src.schemata import (
    BELONG_SCHEMA,
    CREATE_CHAT_SCHEMA,
    CREATE_INTERVIEW_PAIRS_SCHEMA,
    CREATE_QUESTION_RECORD_SCHEMA,
    CREATE_USER_SCHEMA,
    GET_CHAT_SCHEMA,
    GET_INTERVIEW_PAIRS_FOR_USER_SCHEMA,
    GET_QUESTION_RECORD_SCHEMA,
    GET_QUESTION_RECORDS_SCHEMA,
    GET_USER_SCHEMA,
    MIGRATE_CHAT_SCHEMA,
    OPT_IN_OUT_SCHEMA,
    QUESTION_URL_RULE,
    SWAP_INTERVIEW_PAIRS_SCHEMA,
    UUID_RULE,
    UUIDS_RULE,
    validate_input,
)
from src.utils import (
    QuestionInfo,
    SummaryType,
    get_start_of_last_week,
    get_start_of_month,
    get_start_of_week,
)


class UserService:
    def __init__(self, config: Config):
        self.config = config

    @validate_input(CREATE_USER_SCHEMA)
    def create_if_not_exists(self, full_name: str, telegram_id: str) -> dict:
        with session_scope() as session:
            user: Optional[User] = (
                session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
            )
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
            user: Optional[User] = (
                session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
            )
            if user is None:
                raise ResourceNotFoundException()
            user_dict = user.asdict()
        return user_dict

    @validate_input({"id": UUID_RULE})
    def get_user_by_id(self, id: str) -> dict:
        with session_scope() as session:
            user: Optional[User] = session.query(User).filter_by(id=id).one_or_none()
            if user is None:
                raise ResourceNotFoundException()
            user_dict = user.asdict()
        return user_dict

    @validate_input({"ids": UUIDS_RULE})
    def get_users_by_id(self, ids: list[str]) -> list[dict]:
        with session_scope() as session:
            users: list[User] = session.query(User).filter(User.id.in_(ids)).all()
            if len(users) != len(ids):
                raise ResourceNotFoundException()
            user_dicts = [user.asdict() for user in users]
        return user_dicts


class QuestionRecordService:
    def __init__(self, config: Config):
        self.config = config

    @validate_input(CREATE_QUESTION_RECORD_SCHEMA)
    def create_question_record(
        self, user_id: str, platform: str, question_name: str, difficulty: str
    ) -> dict:
        with session_scope() as session:
            user = session.query(User).get(user_id)
            if user is None:
                raise ResourceNotFoundException()

            question_record = QuestionRecord(
                user_id=user_id,
                platform=platform,
                question_name=question_name,
                difficulty=difficulty,
            )

            session.add(question_record)
            session.commit()

            return question_record.asdict()

    @validate_input(GET_QUESTION_RECORD_SCHEMA)
    def get_records_by_user(
        self,
        user_id: str,
        summary_type: Optional[SummaryType] = None,
        is_last_week: bool = False,
    ) -> list[dict]:
        before_date = self.__get_before_date(summary_type, is_last_week=is_last_week)
        after_date = self.__get_after_date(summary_type) if is_last_week else None

        with session_scope() as session:
            query = session.query(QuestionRecord).filter_by(user_id=user_id)
            if before_date is not None:
                query = query.filter(QuestionRecord.created_at >= before_date)
            if after_date is not None:
                query = query.filter(QuestionRecord.created_at < after_date)
            if summary_type == SummaryType.ALL_UNIQUE:
                query = query.distinct(
                    QuestionRecord.question_name,
                    QuestionRecord.platform,
                    QuestionRecord.difficulty,
                )
                question_records = query.all()
            else:
                question_records = query.order_by(QuestionRecord.created_at).all()

            return [question_record.asdict() for question_record in question_records]

    @validate_input(GET_QUESTION_RECORDS_SCHEMA)
    def get_records_by_users(
        self,
        user_ids: list[str],
        summary_type: Optional[SummaryType] = None,
        is_last_week: bool = False,
    ) -> dict:
        before_date = self.__get_before_date(summary_type, is_last_week=is_last_week)
        after_date = self.__get_after_date(summary_type) if is_last_week else None

        with session_scope() as session:
            subquery = session.query(QuestionRecord)
            if before_date is not None:
                subquery = subquery.filter(QuestionRecord.created_at >= before_date)
            if after_date is not None:
                subquery = subquery.filter(QuestionRecord.created_at < after_date)
            question_alias = aliased(QuestionRecord, subquery.subquery())

            query = (
                session.query(User, question_alias)
                .filter(User.id.in_(user_ids))
                .outerjoin(question_alias, question_alias.user_id == User.id)
            )

            if summary_type == SummaryType.ALL_UNIQUE:
                query = query.distinct(
                    question_alias.question_name,
                    question_alias.platform,
                    question_alias.difficulty,
                )
                user_record_pairs = query.all()
            else:
                user_record_pairs = query.order_by(question_alias.created_at).all()

            results: dict[str, dict] = {}
            for user, question_record in user_record_pairs:
                user_dict = user.asdict()
                results[user_dict["id"]] = results.get(
                    user_dict["id"],
                    {"full_name": user_dict["full_name"], "question_records": []},
                )
                if question_record is None:
                    results[user_dict["id"]]["question_records"].clear()
                else:
                    results[user_dict["id"]]["question_records"].append(
                        question_record.asdict()
                    )
            return results

    def __get_before_date(
        self, summary_type: Optional[SummaryType], is_last_week: bool = False
    ) -> Optional[datetime]:
        if summary_type == SummaryType.WEEKLY:
            return get_start_of_last_week() if is_last_week else get_start_of_week()
        elif summary_type == SummaryType.MONTHLY:
            return get_start_of_month()
        return None

    def __get_after_date(
        self, summary_type: Optional[SummaryType]
    ) -> Optional[datetime]:
        if summary_type == SummaryType.WEEKLY:
            return get_start_of_week()
        return None


class ChatService:
    def __init__(self, config: Config):
        self.config = config

    @validate_input(CREATE_CHAT_SCHEMA)
    def create_if_not_exists(self, title: str, telegram_id: str) -> dict:
        with session_scope() as session:
            chat: Optional[Chat] = (
                session.query(Chat).filter_by(telegram_id=telegram_id).one_or_none()
            )
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
            chat: Optional[Chat] = (
                session.query(Chat).filter_by(telegram_id=telegram_id).one_or_none()
            )
            if chat is None:
                raise ResourceNotFoundException()
            chat_dict = chat.asdict()
        return chat_dict

    @validate_input(MIGRATE_CHAT_SCHEMA)
    def migrate_chat_telegram_id(
        self, old_telegram_id: str, new_telegram_id: str
    ) -> dict:
        with session_scope() as session:
            chat: Optional[Chat] = (
                session.query(Chat).filter_by(telegram_id=old_telegram_id).one_or_none()
            )
            if chat is None:
                raise ResourceNotFoundException()

            chat.telegram_id = new_telegram_id

            session.commit()
            chat_dict = chat.asdict()
        return chat_dict


class BelongService:
    def __init__(self, config: Config):
        self.config = config

    @validate_input(BELONG_SCHEMA)
    def add_user_to_chat_if_not_inside(self, user_id: str, chat_id: str) -> dict:
        with session_scope() as session:
            belong: Optional[Belong] = (
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
    def get_users_in_chat(self, chat_id: str) -> list[dict]:
        with session_scope() as session:
            users = [
                {**u.asdict(), "is_opted_out": b.is_opted_out}
                for (u, b) in session.query(User, Belong)
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

    @validate_input(BELONG_SCHEMA)
    def is_user_opted_out(self, user_id: str, chat_id: str) -> bool:
        with session_scope() as session:
            belong: Optional[Belong] = (
                session.query(Belong)
                .filter_by(user_id=user_id, chat_id=chat_id)
                .one_or_none()
            )
            if belong is None:
                raise ResourceNotFoundException()
            return belong.is_opted_out

    @validate_input(OPT_IN_OUT_SCHEMA)
    def opt_in_out(self, user_id: str, chat_id: str, should_opt_out: bool) -> dict:
        with session_scope() as session:
            belong: Optional[Belong] = (
                session.query(Belong)
                .filter_by(user_id=user_id, chat_id=chat_id)
                .one_or_none()
            )
            if belong is None:
                raise ResourceNotFoundException()
            belong.is_opted_out = should_opt_out
            session.commit()
            return belong.asdict()


class InterviewPairService:
    def __init__(self, config: Config):
        self.config = config

    @validate_input(CREATE_INTERVIEW_PAIRS_SCHEMA)
    def add_pairs_for_chat(self, pairs: list[list[str]], chat_id: str):
        monday = get_start_of_week()
        with session_scope() as session:
            session.add_all(
                [
                    InterviewPair(
                        user_one_id=user_one_id,
                        user_two_id=user_two_id,
                        chat_id=chat_id,
                        started_at=monday,
                    )
                    for user_one_id, user_two_id in pairs
                ]
            )

    @validate_input(
        {"chat_id": UUID_RULE, "is_last_week": {"type": "boolean", "required": False}}
    )
    def get_pairs_for_chat(
        self, chat_id: str, is_last_week: bool = False
    ) -> list[dict]:
        before_date = get_start_of_last_week() if is_last_week else get_start_of_week()
        after_date = get_start_of_week() if is_last_week else datetime.now()
        with session_scope() as session:
            pairs = (
                session.query(InterviewPair)
                .filter(InterviewPair.chat_id == chat_id)
                .filter(InterviewPair.started_at >= before_date)
                .filter(InterviewPair.started_at < after_date)
                .all()
            )
            return [pair.asdict() for pair in pairs]

    @validate_input(GET_INTERVIEW_PAIRS_FOR_USER_SCHEMA)
    def get_pairs_for_user(self, user_id: str, is_current: bool = True) -> list[dict]:
        monday = get_start_of_week()
        with session_scope() as session:
            query = (
                session.query(InterviewPair)
                .filter(
                    or_(
                        InterviewPair.user_one_id == user_id,
                        InterviewPair.user_two_id == user_id,
                    )
                )
                .order_by(InterviewPair.created_at)
            )
            if is_current:
                query = query.filter(InterviewPair.started_at >= monday)
            pairs = query.all()
            results = []
            for pair in pairs:
                pair_dict = pair.asdict()
                entry = {}
                for key, value in pair_dict.items():
                    if key not in [
                        "user_one_id",
                        "user_two_id",
                        "user_one_name",
                        "user_two_name",
                    ]:
                        entry[key] = value

                entry["self_id"] = user_id
                entry["self_name"] = (
                    pair_dict["user_one_name"]
                    if pair_dict["user_one_id"] == user_id
                    else pair_dict["user_two_name"]
                )
                entry["partner_id"] = (
                    pair_dict["user_two_id"]
                    if pair_dict["user_one_id"] == user_id
                    else pair_dict["user_one_id"]
                )
                entry["partner_name"] = (
                    pair_dict["user_two_name"]
                    if pair_dict["user_one_id"] == user_id
                    else pair_dict["user_one_name"]
                )

                results.append(entry)

            return results

    @validate_input({"id": UUID_RULE})
    def mark_pair_as_completed(self, id: str) -> dict:
        with session_scope() as session:
            interview_pair: InterviewPair = session.query(InterviewPair).get(id)
            if interview_pair is None:
                raise ResourceNotFoundException()

            interview_pair.is_completed = True

            session.commit()
            return interview_pair.asdict()

    @validate_input(SWAP_INTERVIEW_PAIRS_SCHEMA)
    def swap_pairs_for_users(
        self,
        user_one_id: str,
        user_two_id: str,
        pair_one_id: Optional[str] = None,
        pair_two_id: Optional[str] = None,
    ) -> list[Optional[dict]]:
        with session_scope() as session:
            pair_one: Optional[InterviewPair] = None
            pair_two: Optional[InterviewPair] = None
            if pair_one_id is not None:
                pair_one = session.query(InterviewPair).get(pair_one_id)
                if pair_one is None:
                    raise ResourceNotFoundException()
                if pair_one.user_one_id == user_one_id:
                    pair_one.user_one_id = user_two_id
                else:
                    pair_one.user_two_id = user_two_id
            if pair_two_id is not None:
                pair_two = session.query(InterviewPair).get(pair_two_id)
                if pair_two is None:
                    raise ResourceNotFoundException()
                if pair_two.user_one_id == user_two_id:
                    pair_two.user_one_id = user_one_id
                else:
                    pair_two.user_two_id = user_one_id
            session.commit()
            return [
                pair_one.asdict() if pair_one is not None else None,
                pair_two.asdict() if pair_two is not None else None,
            ]


class QuestionInfoService:
    def __init__(self, config: Config):
        self.config = config
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        )
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(), options=chrome_options
        )

    @validate_input({"url": QUESTION_URL_RULE, "is_leetcode": {"type": "boolean"}})
    def get_question_info(self, url: str, is_leetcode: bool) -> QuestionInfo:
        fetch_url = self.__get_fetch_url(url=url)
        self.driver.get(fetch_url)
        sleep(0.5)
        page_name = str(self.driver.title)

        if self.__is_invalid_page_name(page_name):
            question_name = self.__parse_url_directly(url, is_leetcode)
            return QuestionInfo(question_name, None)

        question_name = page_name[:-11] if is_leetcode else page_name[:-13]
        difficulty = self.__get_difficulty(is_leetcode)

        return QuestionInfo(question_name, difficulty)

    @validate_input({"url": QUESTION_URL_RULE})
    def __get_fetch_url(self, url: str) -> str:
        url_split = url.split(".com/")
        path_split = url_split[1].split("/")
        path = path_split[0] + "/" + path_split[1]
        fetch_url = url_split[0] + ".com/" + path
        return fetch_url

    def __is_invalid_page_name(self, page_name: str) -> bool:
        if not page_name:
            return True
        page_name = page_name.lower()
        invalid_strings = ["account login", "access denied", "page not found"]
        for invalid_string in invalid_strings:
            if invalid_string in page_name:
                return True
        return len(page_name) <= 11

    def __parse_url_directly(self, url: str, is_leetcode: bool) -> Optional[str]:
        split_url = (
            url.split("/problems/") if is_leetcode else url.split("/challenges/")
        )
        if len(split_url) < 2:
            return None
        question_name_kebab = split_url[1].split("/")[0]
        question_name_split = question_name_kebab.split("-")
        question_name = " ".join(list(map(lambda x: x.title(), question_name_split)))

        if question_name[-1] == "/":
            question_name = question_name[:-1]

        return question_name

    def __get_difficulty(self, is_leetcode: bool) -> Optional[str]:
        difficulties = ["easy", "medium", "hard"]
        for difficulty in difficulties:
            difficulty = difficulty.title() if is_leetcode else difficulty
            try:
                _ = self.driver.find_element_by_css_selector(
                    (
                        f"span.difficulty-label.label-{difficulty}"
                        if is_leetcode
                        else f"div.difficulty-block > p.difficulty-{difficulty}"
                    )
                )
                return difficulty.lower()
            except NoSuchElementException:
                continue
        return None


class Services:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.user_service = UserService(config)
        self.chat_service = ChatService(config)
        self.belong_service = BelongService(config)
        self.question_record_service = QuestionRecordService(config)
        self.pair_service = InterviewPairService(config)
        self.question_info_service = QuestionInfoService(config)
        self.logger = logger


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

stdout_handler = logging.StreamHandler(stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.addFilter(lambda record: record.levelno == logging.INFO)
stderr_handler = logging.StreamHandler()
stderr_handler.setLevel(logging.WARNING)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stdout_handler.setFormatter(formatter)
stderr_handler.setFormatter(formatter)

logger.addHandler(stdout_handler)
logger.addHandler(stderr_handler)

SERVICES = Services(APP_CONFIG, logger)
