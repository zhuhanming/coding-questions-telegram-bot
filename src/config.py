from os import getenv

from dotenv import load_dotenv

load_dotenv()

BOT_ENV = getenv("BOT_ENV")
DATABASE_URL = getenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

APP_CONFIG = {
    "DATABASE_URL": DATABASE_URL,
    "BOT_ACCESS_TOKEN": getenv("BOT_ACCESS_TOKEN"),
    "DEVELOPER_ID": getenv("DEVELOPER_ID"),
    "WEEKLY_TARGET": 7,
    "TRACEBACK_LENGTH": 300,
    "PLATFORM_KEY": "PLATFORM",
    "QUESTION_NAME_KEY": "QUESTION_NAME",
}
