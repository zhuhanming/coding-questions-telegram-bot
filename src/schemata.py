from functools import wraps

from cerberus import Validator  # type: ignore

from src.exceptions import InvalidRequestException


def validate_input(schema, **validator_kwargs):
    def decorator(func):
        @wraps(func)
        def decorated_func(*args, **kwargs):
            validator = Validator(schema, require_all=True, **validator_kwargs)
            res = validator.validate(kwargs)
            if not res:
                raise InvalidRequestException(validator.errors)

            return func(*args, **kwargs)

        return decorated_func

    return decorator


UUID_REGEX = (
    "[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}"
)
TELEGRAM_USER_ID_REGEX = "^[0-9]+$"
LEETCODE_REGEX = "^((https?):\/\/)?(www.)?leetcode\.com/problems+(\/[a-zA-Z0-9-]+\/?)*$"
HACKERRANK_REGEX = (
    "^((https?):\/\/)?(www.)?hackerrank\.com/challenges+(\/[a-zA-Z0-9-]+\/?)*$"
)

UUID_RULE = {"type": "string", "regex": UUID_REGEX}
UUIDS_RULE = {"type": "list", "regex": UUID_REGEX}
TELEGRAM_USER_ID_RULE = {"type": "string", "regex": TELEGRAM_USER_ID_REGEX}
QUESTION_URL_RULE = {
    "type": "string",
    "anyof_regex": [LEETCODE_REGEX, HACKERRANK_REGEX],
}

CREATE_USER_SCHEMA = {
    "full_name": {"type": "string"},
    "telegram_id": TELEGRAM_USER_ID_RULE,
}
GET_USER_SCHEMA = {"telegram_id": TELEGRAM_USER_ID_RULE}

CREATE_CHAT_SCHEMA = {"title": {"type": "string"}, "telegram_id": {"type": "string"}}
GET_CHAT_SCHEMA = {"telegram_id": {"type": "string"}}

BELONG_SCHEMA = {"user_id": UUID_RULE, "chat_id": UUID_RULE}

CREATE_QUESTION_RECORD_SCHEMA = {
    "user_id": UUID_RULE,
    "platform": {"type": "string", "allowed": ["leetcode", "hackerrank", "other"]},
    "question_name": {"type": "string"},
    "difficulty": {"type": "string", "allowed": ["easy", "medium", "hard"]},
}
GET_QUESTION_RECORD_SCHEMA = {"user_id": UUID_RULE, "summary_type": {"required": False}}
GET_QUESTION_RECORDS_SCHEMA = {
    "user_ids": UUIDS_RULE,
    "summary_type": {"required": False},
}

CREATE_INTERVIEW_PAIRS_SCHEMA = {
    "pairs": {
        "type": "list",
        "schema": {"type": "list", "items": [UUID_RULE, UUID_RULE]},
    },
    "chat_id": UUID_RULE,
}
