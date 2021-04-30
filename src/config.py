from os import getenv

from dotenv import load_dotenv

load_dotenv()

BOT_ENV = getenv("BOT_ENV")
DEFAULT_DATABASE_URL = ""
if BOT_ENV == "DEVELOPMENT":
    DEFAULT_DATABASE_URL = "postgresql://coding_questions_bot:coding_questions_bot@localhost/coding_questions_bot"
elif BOT_ENV == "TEST":
    DEFAULT_DATABASE_URL = "postgresql://coding_questions_bot:coding_questions_bot@localhost/coding_questions_bot_test"
DATABASE_URL = getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

APP_CONFIG = {
    "DATABASE_URL": DATABASE_URL,
    "BOT_ACCESS_TOKEN": getenv("BOT_ACCESS_TOKEN"),
    "DEVELOPER_ID": getenv("DEVELOPER_ID"),
    "WEEKLY_TARGET": 7,
    "PLATFORM_KEY": "PLATFORM",
    "TRACEBACK_LENGTH": 3000,
    "QUESTION_NAME_KEY": "QUESTION_NAME",
    "BOT_URL": "http://t.me/CodingQuestionsBot",
}
