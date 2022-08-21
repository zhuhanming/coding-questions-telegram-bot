from warnings import filterwarnings

from telegram import BotCommandScopeAllGroupChats, BotCommandScopeDefault
from telegram.ext import Application, PicklePersistence
from telegram.warnings import PTBUserWarning

from src.config import APP_CONFIG
from src.handlers import (
    AddMeHandler,
    AddQuestionHandler,
    ChatCreatedHandler,
    CompleteInterviewHandler,
    ErrorHandler,
    IndividualStatsHandler,
    LeftChatMemberHandler,
    MembersHandler,
    MigrateHandler,
    NewChatMembersHandler,
    OptInOutHandler,
    PaginationHandler,
    StartHandler,
    UnknownMessageHandler,
)
from src.helpers import AppHelper
from src.services import AppService

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)


async def post_init(application: Application) -> None:
    await application.bot.delete_my_commands()
    await application.bot.set_my_commands(
        commands=APP_CONFIG["PRIVATE_COMMANDS"], scope=BotCommandScopeDefault()
    )
    await application.bot.set_my_commands(
        commands=APP_CONFIG["GROUP_COMMANDS"], scope=BotCommandScopeAllGroupChats()
    )


# TODO: Improve logging
# TODO: Make app more friendly
def main() -> None:
    """Start the bot."""
    # Initialise the app components
    APP_SERVICE = AppService()
    APP_HELPER = AppHelper()
    persistence = PicklePersistence(filepath="persistence")

    # Create the Application and pass it the bot's token.
    application = (
        Application.builder()
        .token(APP_CONFIG["BOT_ACCESS_TOKEN"])
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )

    # Individual chat command handlers
    StartHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    AddQuestionHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    CompleteInterviewHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    IndividualStatsHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    OptInOutHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)

    # Group chat command handlers
    MembersHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    AddMeHandler(APP_SERVICE, APP_HELPER, APP_CONFIG).bind(application)
    # Stats - handle questions + interviews, this week + last week
    # Generate pairs - allow for swapping
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
