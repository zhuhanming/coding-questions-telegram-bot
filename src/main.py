from telegram.ext import Application

from src.config import APP_CONFIG
from src.handlers import StartHandler
from src.helpers import AppHelper
from src.services import AppService


def main() -> None:
    """Start the bot."""
    # Initialise the app components
    APP_SERVICE = AppService()
    APP_HELPER = AppHelper()

    # Create the Application and pass it the bot's token.
    application = Application.builder().token(APP_CONFIG["BOT_ACCESS_TOKEN"]).build()

    # on different commands - answer in Telegram
    StartHandler(application, APP_SERVICE, APP_HELPER, APP_CONFIG)

    # Run the bot until the user presses Ctrl-C
    APP_HELPER.logger.info("The application is up and running")
    application.run_polling()


if __name__ == "__main__":
    main()
