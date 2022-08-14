from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from .base import BaseHandler


class MigrateHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(
            MessageHandler(
                filters.StatusUpdate.MIGRATE & filters.ChatType.GROUPS,
                self.migrate,
            )
        )

    async def migrate(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = self._get_message(update)
        chat = self._get_chat(update)
        if message.migrate_from_chat_id is None:
            # Fail silently
            return

        chat_dict = self.service.chat.migrate_chat_telegram_id(
            old_telegram_id=str(message.migrate_from_chat_id),
            new_telegram_id=str(chat.id),
        )
        self.helper.logger.info(f"Migrated {chat_dict['title']}")
