from telegram.ext import Application

from src.config import APP_CONFIG
from src.handlers import (
    AddQuestionHandler,
    CompleteInterviewHandler,
    StartHandler,
    StatsHandler,
    UnknownMessageHandler,
)
from src.helpers import AppHelper
from src.services import AppService


def main() -> None:
    """Start the bot."""
    # Initialise the app components
    APP_SERVICE = AppService()
    APP_HELPER = AppHelper()

    # Create the Application and pass it the bot's token.
    application = Application.builder().token(APP_CONFIG["BOT_ACCESS_TOKEN"]).build()

    # Individual chat command handlers
    StartHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    AddQuestionHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    CompleteInterviewHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    StatsHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)

    # General command handlers
    UnknownMessageHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)

    # Run the bot until the user presses Ctrl-C
    APP_HELPER.logger.info("The application is up and running")
    application.run_polling()


if __name__ == "__main__":
    main()
