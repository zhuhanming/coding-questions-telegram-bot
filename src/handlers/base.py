from abc import ABC, abstractmethod
from typing import Any, cast

from telegram import CallbackQuery, Chat, InlineKeyboardMarkup, Message, Update, User
from telegram.error import BadRequest
from telegram.ext import Application, ContextTypes

from ..config import Config
from ..helpers import AppHelper
from ..services import AppService
from ..utils import InvalidUserDataException, unwrap


class BaseHandler(ABC):
    def __init__(self, service: AppService, helper: AppHelper, config: Config) -> None:
        self.service = service
        self.helper = helper
        self.config = config

    @abstractmethod
    def bind(self, app: Application) -> None:
        pass

    # Helper methods for Telegram's Context object
    def _get_context_value(self, context: ContextTypes.DEFAULT_TYPE, key: str) -> Any:
        if context.user_data is None:
            raise InvalidUserDataException()
        return context.user_data.get(key, None)

    def _set_context_value(
        self, context: ContextTypes.DEFAULT_TYPE, key: str, value: Any
    ) -> None:
        if context.user_data is None:
            raise InvalidUserDataException()
        context.user_data[key] = value

    def _clear_context_values(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        if context.user_data is None:
            raise InvalidUserDataException()
        context.user_data.clear()

    # Helper methods for caching the previous message ID
    def _get_previous_message_id(
        self, context: ContextTypes.DEFAULT_TYPE
    ) -> int | None:
        return cast(int | None, self._get_context_value(context, "PREVIOUS_MESSAGE_ID"))

    def _set_previous_message_id(
        self, context: ContextTypes.DEFAULT_TYPE, message: Message | bool
    ) -> None:
        if type(message) is not bool:
            self._set_context_value(context, "PREVIOUS_MESSAGE_ID", message.id)

    # Helper get methods for Telegram's Update object
    async def _get_and_answer_query(self, update: Update) -> CallbackQuery:
        query = unwrap(update.callback_query)
        await query.answer()
        return query

    def _get_user(self, update: Update) -> User:
        return unwrap(update.effective_user)

    def _get_message(self, update: Update) -> Message:
        return unwrap(update.effective_message)

    def _get_message_text(self, update: Update) -> str:
        return unwrap(self._get_message(update).text)

    def _get_chat(self, update: Update) -> Chat:
        return unwrap(self._get_message(update).chat)

    def _get_error(self, context: ContextTypes.DEFAULT_TYPE) -> Exception:
        return unwrap(context.error)

    async def _clear_previous_message_reply_markup(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        previous_message_id = self._get_previous_message_id(context)
        if previous_message_id is None:
            return

        try:
            await context.bot.edit_message_reply_markup(
                self._get_chat(update).id,
                previous_message_id,
                reply_markup=None,
            )
        except BadRequest:
            self.helper.logger.error("Tried to clear an already cleared reply markup")

    # Helper methods for sending and editing messages
    async def _reply_text(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        message: Message,
        reply_text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> Message:
        new_message = await message.reply_text(
            reply_text,
            reply_markup=reply_markup,
        )
        self._set_previous_message_id(context, new_message)
        return cast(Message, new_message)

    async def _edit_query_text(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        query: CallbackQuery,
        edit_text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> Message:
        new_message = await query.edit_message_text(
            edit_text,
            reply_markup=reply_markup,
        )
        self._set_previous_message_id(context, new_message)
        return cast(Message, new_message)

    async def _edit_message_text(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        message: Message,
        edit_text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> Message:
        new_message = await message.edit_text(
            edit_text,
            reply_markup=reply_markup,
        )
        self._set_previous_message_id(context, new_message)
        return cast(Message, new_message)
