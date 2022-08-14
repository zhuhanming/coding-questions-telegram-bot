from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from ..utils import MONTH_ALL_SUMMARY_STRFTIME_FORMAT, SummaryType, format_platform_name
from .base import BaseHandler


class ViewStatsHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(CallbackQueryHandler(self.view_stats, "view_stats"))
        app.add_handler(CallbackQueryHandler(self.all_questions, "all_questions"))

    async def view_stats(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = await self._get_and_answer_query(update)
        await self._edit_query_text(
            context,
            query,
            "What stats would you like to see?",
            self.__get_stats_keyboard(),
        )

    async def all_questions(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = await self._get_and_answer_query(update)
        user = self._get_user(update)
        user_dict = self.service.user.create_if_not_exists(
            full_name=user.full_name, telegram_id=str(user.id)
        )
        records = self.service.question_record.get_records_by_user(
            user_id=user_dict["id"], summary_type=SummaryType.ALL
        )
        if not records:
            await self._edit_query_text(
                context,
                query,
                "You have not completed any questions!",
                InlineKeyboardMarkup(self.__get_back_keyboard()),
            )

        header_text = "Questions you have completed all time"
        items = [
            f'{record["question_name"]} [{record["difficulty"].title()}] [{format_platform_name(record["platform"])}] ({record["created_at"].strftime(MONTH_ALL_SUMMARY_STRFTIME_FORMAT)})'
            for record in records
        ]
        pagination = self.helper.pagination.create_and_set_data(
            header_text, items, 20, None, self.__get_back_keyboard()
        )
        text, keyboard = pagination.generate_message(0)
        await self._edit_query_text(context, query, text, keyboard)

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

    def __get_back_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return [[InlineKeyboardButton(text="Back", callback_data="view_stats")]]
