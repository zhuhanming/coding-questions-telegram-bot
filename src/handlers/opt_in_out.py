from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

from ..utils import InvalidUserDataException, OptInOutType
from .base import BaseHandler

CHAT_SELECTED = 0


class OptInOutHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(
            ConversationHandler(
                entry_points=[CallbackQueryHandler(self.opt_in_out, "opt_in_out")],
                states={
                    CHAT_SELECTED: [
                        CallbackQueryHandler(
                            self.chat_selected, "^chat_\d+(_(questions|interviews))?$"
                        )
                    ],
                },
                fallbacks=[CallbackQueryHandler(self.cancel, "cancel")],
                # We want them to be able to go from CHAT_SELECTED back to entry point at any time
                allow_reentry=True,
                # The below settings don't really matter since we're assuming that the add_question
                # occurs in private chats, but this is just for sanity reasons.
                # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Frequently-Asked-Questions#what-do-the-per_-settings-in-conversationhandler-do
                per_chat=True,
                per_user=True,
                per_message=False,  # We only want a single conversation to occur
            )
        )

    async def opt_in_out(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = await self._get_and_answer_query(update)
        user = self._get_user(update)

        user_dict = self.service.user.get_user_by_telegram_id(telegram_id=str(user.id))
        chat_dicts = self.service.belong.get_chats_for_user(user_id=user_dict["id"])
        self._set_context_value(context, "CHATS", chat_dicts)

        header_text = "Select a chat to manage"
        items = [chat_dict["title"] for chat_dict in chat_dicts]
        chat_to_button_mapper = lambda chat, index: InlineKeyboardButton(
            text=chat, callback_data=f"chat_{index}"
        )
        pagination = self.helper.pagination.create_and_set_data(
            header_text,
            items,
            5,
            chat_to_button_mapper,
            self.__get_back_to_start_keyboard(),
        )
        text, keyboard = pagination.generate_message(0)
        await self._edit_query_text(context, query, text, keyboard)
        return CHAT_SELECTED

    async def chat_selected(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = await self._get_and_answer_query(update)
        user = self._get_user(update)
        data = str(query.data).split("_")
        if len(data) < 2:
            raise InvalidUserDataException

        user_dict = self.service.user.get_user_by_telegram_id(telegram_id=str(user.id))
        chat_index = int(data[1], 10)
        chat_dicts = self._get_context_value(context, "CHATS")
        chat_dict = chat_dicts[chat_index]

        if len(data) == 3:
            opt_in_out_type = (
                OptInOutType.QUESTIONS
                if data[2] == "questions"
                else OptInOutType.INTERVIEWS
            )
            self.service.belong.toggle_opt_in_out(
                user_id=user_dict["id"],
                chat_id=chat_dict["id"],
                opt_in_out_type=opt_in_out_type,
            )

        status = self.service.belong.get_opt_in_out_status(
            user_id=user_dict["id"], chat_id=chat_dict["id"]
        )
        keyboard = self.__get_opt_in_out_keyboard(status, chat_index)
        await self._edit_query_text(
            context,
            query,
            f"Settings for {chat_dict['title']}:\n\n"
            f"Questions: Opted {'Out' if status[OptInOutType.QUESTIONS] else 'In'}\n"
            f"Interviews: Opted {'Out' if status[OptInOutType.INTERVIEWS] else 'In'}\n",
            keyboard,
        )
        return CHAT_SELECTED

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = await self._get_and_answer_query(update)
        await self._edit_query_text(
            context,
            query,
            "Hope you've managed to configure your opt in/out statuses!\n\n"
            "How else can I help you?",
            self.__get_final_keyboard(),
        )
        self._clear_context_values(context)
        return ConversationHandler.END

    def __get_back_to_start_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return [[InlineKeyboardButton(text="Cancel", callback_data="cancel")]]

    def __get_opt_in_out_keyboard(
        self, status: dict[OptInOutType, bool], chat_index: int
    ) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=f"Opt {'in' if status[OptInOutType.QUESTIONS] else 'out'} for questions",
                        callback_data=f"chat_{chat_index}_questions",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=f"Opt {'in' if status[OptInOutType.INTERVIEWS] else 'out'} for interviews",
                        callback_data=f"chat_{chat_index}_interviews",
                    )
                ],
                [InlineKeyboardButton(text="Back", callback_data="opt_in_out")],
            ]
        )

    def __get_final_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Add a question", callback_data="add_question"
                    ),
                    InlineKeyboardButton(
                        text="Complete an interview", callback_data="complete_interview"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Opt in/out again", callback_data="opt_in_out"
                    ),
                    InlineKeyboardButton(
                        text="View stats", callback_data="individual_stats"
                    ),
                ],
            ]
        )
