from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

from .base import BaseHandler

CONFIRM = 0


class CompleteInterviewHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(
            ConversationHandler(
                entry_points=[
                    CallbackQueryHandler(self.complete_interview, "complete_interview")
                ],
                states={CONFIRM: [CallbackQueryHandler(self.confirm, "^\d+$")]},
                fallbacks=[CallbackQueryHandler(self.cancel, "cancel")],
                # There are scenarios where a user does some unexpected action and ends up being
                # pulled out from the conversation halfway. This allows them to restart the
                # conversation from the entry point.
                allow_reentry=True,
            )
        )

    async def complete_interview(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = await self._get_and_answer_query(update)
        user = self._get_user(update)
        user_dict = self.service.user.get_user_by_telegram_id(telegram_id=str(user.id))
        pairs = self.service.pair.get_pairs_for_user(user_id=user_dict["id"])

        if len(pairs) == 0:
            await self._edit_query_text(
                context,
                query,
                "You have no mock interview partners arranged through me for this week!\n\n"
                "To get paired, please use /interview_pairs in a chat group first.",
                self.__get_final_keyboard(show_interview_button=False),
            )
            return ConversationHandler.END

        incomplete_pairs = list(filter(lambda x: not x["is_completed"], pairs))
        self._set_context_value(context, "INCOMPLETE_PAIRS", incomplete_pairs)

        if len(incomplete_pairs) == 0:
            await self._edit_query_text(
                context,
                query,
                "It seems like you've completed all your mock interviews this week! "
                "It may have been your partner who marked this interview as completed.\n\n"
                "You can view stats to see all mock interviews you've arranged through me.",
                self.__get_final_keyboard(show_interview_button=False),
            )
            return ConversationHandler.END

        return CONFIRM

    async def confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = await self._get_and_answer_query(update)
        await self._edit_query_text(
            context,
            query,
            "No worries! Feel free to complete another interview when you're ready!\n\n"
            "How else can I help you?",
            self.__get_final_keyboard(),
        )
        self._clear_context_values(context)
        return ConversationHandler.END

    def __get_final_keyboard(
        self, show_interview_button: bool = True
    ) -> InlineKeyboardMarkup:
        buttons = [
            [InlineKeyboardButton(text="Add question", callback_data="add_question")],
            [InlineKeyboardButton(text="View stats", callback_data="view_stats")],
        ]
        if show_interview_button:
            buttons.insert(
                1,
                [
                    InlineKeyboardButton(
                        text="Complete another interview",
                        callback_data="complete_interview",
                    )
                ],
            )
        return InlineKeyboardMarkup(buttons)
