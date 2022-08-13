from datetime import datetime

from sqlalchemy.sql.expression import or_

from ..database import InterviewPair, session_scope
from ..utils import (
    TIMEZONE,
    UUID_REGEX,
    UUID_RULE,
    ResourceNotFoundException,
    get_start_of_last_week,
    get_start_of_week,
    validate_input,
)

CREATE_INTERVIEW_PAIRS_SCHEMA = {
    "pairs": {
        "type": "list",
        "schema": {"type": "list", "items": [UUID_RULE, UUID_RULE]},
    },
    "chat_id": UUID_RULE,
}
GET_INTERVIEW_PAIRS_FOR_CHAT_SCHEMA = {
    "chat_id": UUID_RULE,
    "is_last_week": {"type": "boolean", "required": False},
}
GET_INTERVIEW_PAIRS_FOR_USER_SCHEMA = {
    "user_id": UUID_RULE,
    "is_current": {"type": "boolean", "required": False},
}
MARK_INTERVIEW_PAIR_AS_COMPLETED_SCHEMA = {"id": UUID_RULE}
SWAP_INTERVIEW_PAIRS_SCHEMA = {
    "user_one_id": UUID_RULE,
    "user_two_id": UUID_RULE,
    "pair_one_id": {"type": "string", "nullable": True, "regex": UUID_REGEX},
    "pair_two_id": {"type": "string", "nullable": True, "regex": UUID_REGEX},
}


class InterviewPairService:
    @validate_input(CREATE_INTERVIEW_PAIRS_SCHEMA)
    def add_pairs_for_chat(self, pairs: list[list[str]], chat_id: str) -> None:
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
            session.commit()

    @validate_input(GET_INTERVIEW_PAIRS_FOR_CHAT_SCHEMA)
    def get_pairs_for_chat(
        self, chat_id: str, is_last_week: bool = False
    ) -> list[dict]:
        before_date = get_start_of_last_week() if is_last_week else get_start_of_week()
        after_date = get_start_of_week() if is_last_week else datetime.now(tz=TIMEZONE)
        with session_scope() as session:
            pairs = (
                session.query(InterviewPair)
                .filter(InterviewPair.chat_id == chat_id)
                .filter(InterviewPair.started_at >= before_date)
                .filter(InterviewPair.started_at < after_date)
                .all()
            )
        return [pair.as_dict() for pair in pairs]

    @validate_input(GET_INTERVIEW_PAIRS_FOR_USER_SCHEMA)
    def get_pairs_for_user(self, user_id: str, is_current: bool = True) -> list[dict]:
        monday = get_start_of_week()
        results = []
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

            excluded_keys = {
                "user_one_id",
                "user_two_id",
                "user_one_name",
                "user_two_name",
            }
            for pair in pairs:
                pair_dict = pair.as_dict()
                entry = {k: pair_dict[k] for k in set(pair_dict.keys()) - excluded_keys}
                entry["self_id"] = user_id
                if pair_dict["user_one_id"] == user_id:
                    entry["self_name"] = pair_dict["user_one_name"]
                    entry["partner_id"] = pair_dict["user_two_id"]
                    entry["partner_name"] = pair_dict["user_two_name"]
                else:
                    entry["self_name"] = pair_dict["user_two_name"]
                    entry["partner_id"] = pair_dict["user_one_id"]
                    entry["partner_name"] = pair_dict["user_one_name"]

                results.append(entry)
        return results

    @validate_input(MARK_INTERVIEW_PAIR_AS_COMPLETED_SCHEMA)
    def mark_pair_as_completed(self, id: str) -> dict:
        with session_scope() as session:
            interview_pair: InterviewPair = session.query(InterviewPair).get(id)
            if interview_pair is None:
                raise ResourceNotFoundException()

            interview_pair.is_completed = True

            session.commit()
        return interview_pair.as_dict()

    # It's possible for the pair ID to be None when the user was originally unpaired.
    @validate_input(SWAP_INTERVIEW_PAIRS_SCHEMA)
    def swap_pairs_for_users(
        self,
        user_one_id: str,
        user_two_id: str,
        pair_one_id: str | None = None,
        pair_two_id: str | None = None,
    ) -> list[dict | None]:
        with session_scope() as session:
            pair_one: InterviewPair | None = None
            pair_two: InterviewPair | None = None

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
            pair_one.as_dict() if pair_one is not None else None,
            pair_two.as_dict() if pair_two is not None else None,
        ]
