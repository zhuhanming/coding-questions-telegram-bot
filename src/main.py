from warnings import filterwarnings

from telegram.ext import Application
from telegram.warnings import PTBUserWarning

from src.config import APP_CONFIG
from src.handlers import (
    AddQuestionHandler,
    ChatCreatedHandler,
    CompleteInterviewHandler,
    ErrorHandler,
    LeftChatMemberHandler,
    MembersHandler,
    MigrateHandler,
    NewChatMembersHandler,
    PaginationHandler,
    StartHandler,
    UnknownMessageHandler,
    ViewStatsHandler,
)
from src.helpers import AppHelper
from src.services import AppService

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)


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
    ViewStatsHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    # Opting in and out

    # Group chat command handlers
    MembersHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    # Add me
    # Stats - handle questions + interviews, this week + last week
    # Generate pairs - allow for regeneration aka reshuffling
    # Swap partners
    # Settings

    # Chat status update handlers
    ChatCreatedHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    NewChatMembersHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    LeftChatMemberHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    MigrateHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)

    # General command handlers
    UnknownMessageHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    PaginationHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    ErrorHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)

    # Run the bot until the user presses Ctrl-C
    APP_HELPER.logger.info("The application is up and running")
    application.run_polling()


if __name__ == "__main__":
    main()
