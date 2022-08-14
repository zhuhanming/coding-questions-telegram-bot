from os import getenv
from typing import TypedDict

from dotenv import load_dotenv

from .utils import unwrap

load_dotenv()

BOT_ENV = getenv("BOT_ENV")
match BOT_ENV:
    case "DEVELOPMENT":
        DEFAULT_DATABASE_URL = "postgresql://coding_questions_bot:coding_questions_bot@localhost/coding_questions_bot"
    case "TEST":
        DEFAULT_DATABASE_URL = "postgresql://coding_questions_bot:coding_questions_bot@localhost/coding_questions_bot_test"
    case _:
        DEFAULT_DATABASE_URL = ""
DATABASE_URL = getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

PRIVATE_COMMANDS = [
    ("start", "Get started with the bot! This is the entry point for everything.")
]
GROUP_COMMANDS = [
    ("members", "See a list of members in the current group."),
    ("add_me", "Add yourself to current group members."),
]

Config = TypedDict(
    "Config",
    {
        "DATABASE_URL": str,
        "BOT_ACCESS_TOKEN": str,
        "DEVELOPER_ID": str,
        "WEEKLY_TARGET": int,
        "TRACEBACK_LENGTH": int,
        "BOT_URL": str,
        "PRIVATE_COMMANDS": list[tuple[str, str]],
        "GROUP_COMMANDS": list[tuple[str, str]],
    },
)

APP_CONFIG: Config = {
    "DATABASE_URL": DATABASE_URL,
    "BOT_ACCESS_TOKEN": unwrap(getenv("BOT_ACCESS_TOKEN")),
    "DEVELOPER_ID": unwrap(getenv("DEVELOPER_ID")),
    "WEEKLY_TARGET": 7,
    "TRACEBACK_LENGTH": 3000,
    "BOT_URL": "http://t.me/CodingQuestionsBot",
    "PRIVATE_COMMANDS": PRIVATE_COMMANDS,
    "GROUP_COMMANDS": GROUP_COMMANDS,
}
