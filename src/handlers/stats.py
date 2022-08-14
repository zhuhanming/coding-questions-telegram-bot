from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from .base import BaseHandler


class StatsHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(CallbackQueryHandler(self.stats, "view_stats"))

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = await self._get_and_answer_query(update)
        await self._edit_query_text(
            context,
            query,
            f"What stats would you like to see?",
            self.__get_stats_keyboard(),
        )

    def __get_stats_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="This week's questions",
                        callback_data="this_week_questions",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Last week's questions",
                        callback_data="last_week_questions",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="This month's questions",
                        callback_data="this_month_questions",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="All questions", callback_data="all_questions"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="All unique questions",
                        callback_data="all_unique_questions",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Past interview pairs", callback_data="past_pairs"
                    )
                ],
                [InlineKeyboardButton(text="Back", callback_data="start")],
            ]
        )
