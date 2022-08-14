from datetime import datetime

from sqlalchemy.orm import aliased

from ..database import QuestionRecord, User, session_scope
from ..utils import (
    UUID_RULE,
    UUIDS_RULE,
    ResourceNotFoundException,
    SummaryType,
    get_start_of_last_week,
    get_start_of_month,
    get_start_of_week,
    validate_input,
)

CREATE_QUESTION_RECORD_SCHEMA = {
    "user_id": UUID_RULE,
    "platform": {"type": "string", "allowed": ["leetcode", "hackerrank", "other"]},
    "question_name": {"type": "string"},
    "difficulty": {"type": "string", "allowed": ["easy", "medium", "hard"]},
}
GET_QUESTION_RECORD_SCHEMA = {
    "user_id": UUID_RULE,
    "summary_type": {"required": False},
    "is_last_week": {"type": "boolean", "required": False},
}
GET_QUESTION_RECORDS_SCHEMA = {
    "user_ids": UUIDS_RULE,
    "summary_type": {"required": False},
    "is_last_week": {"type": "boolean", "required": False},
}


class QuestionRecordService:
    @validate_input(CREATE_QUESTION_RECORD_SCHEMA)
    def create_question_record(
        self, user_id: str, platform: str, question_name: str, difficulty: str
    ) -> dict:
        with session_scope() as session:
            # Do a sanity check to ensure that user exists
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

            return question_record.as_dict()

    @validate_input(GET_QUESTION_RECORD_SCHEMA)
    def get_records_by_user(
        self,
        user_id: str,
        summary_type: SummaryType | None = None,
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

            return [question_record.as_dict() for question_record in question_records]

    # Returns a dictionary with user ID as the key and a list of question records as the value.
    @validate_input(GET_QUESTION_RECORDS_SCHEMA)
    def get_records_by_users(
        self,
        user_ids: list[str],
        summary_type: SummaryType | None = None,
        is_last_week: bool = False,
    ) -> dict[str, dict]:
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
                # The ordering does not matter here since we're looking at unique submissions
                user_record_pairs = query.all()
            else:
                user_record_pairs = query.order_by(question_alias.created_at).all()

            results: dict[str, dict] = {}
            for user, question_record in user_record_pairs:
                user_dict = user.as_dict()
                results[user_dict["id"]] = results.get(
                    user_dict["id"],
                    {"full_name": user_dict["full_name"], "question_records": []},
                )
                if question_record is None:
                    results[user_dict["id"]]["question_records"].clear()
                else:
                    results[user_dict["id"]]["question_records"].append(
                        question_record.as_dict()
                    )
            return results

    def __get_before_date(
        self, summary_type: SummaryType | None, is_last_week: bool = False
    ) -> datetime | None:
        if summary_type == SummaryType.WEEKLY:
            return get_start_of_last_week() if is_last_week else get_start_of_week()
        elif summary_type == SummaryType.MONTHLY:
            return get_start_of_month()
        return None

    def __get_after_date(self, summary_type: SummaryType | None) -> datetime | None:
        if summary_type == SummaryType.WEEKLY:
            return get_start_of_week()
        return None
