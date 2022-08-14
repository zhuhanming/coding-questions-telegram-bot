from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from ..utils import (
    MONTH_ALL_SUMMARY_STRFTIME_FORMAT,
    WEEK_SUMMARY_STRFTIME_FORMAT,
    SummaryType,
    difficulty_to_int,
    format_platform_name,
    platform_to_int,
)
from .base import BaseHandler


class ViewStatsHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(CallbackQueryHandler(self.view_stats, "view_stats"))
        app.add_handler(
            CallbackQueryHandler(self.this_week_questions, "this_week_questions")
        )
        app.add_handler(
            CallbackQueryHandler(self.last_week_questions, "last_week_questions")
        )
        app.add_handler(
            CallbackQueryHandler(self.this_month_questions, "this_month_questions")
        )
        app.add_handler(CallbackQueryHandler(self.all_questions, "all_questions"))
        app.add_handler(
            CallbackQueryHandler(self.all_unique_questions, "all_unique_questions")
        )

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

    async def this_week_questions(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await self.__helper(update, context, SummaryType.WEEKLY)

    async def last_week_questions(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await self.__helper(update, context, SummaryType.WEEKLY, True)

    async def this_month_questions(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await self.__helper(update, context, SummaryType.MONTHLY)

    async def all_questions(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await self.__helper(update, context, SummaryType.ALL)

    async def all_unique_questions(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await self.__helper(update, context, SummaryType.ALL_UNIQUE)

    # TODO: Handle weekly targets of chats
    # TODO: Handle opt-out timings, i.e. time-travelling where necessary
    async def __helper(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        summary_type: SummaryType,
        is_last_week: bool = False,
    ) -> None:
        query = await self._get_and_answer_query(update)
        user = self._get_user(update)
        user_dict = self.service.user.create_if_not_exists(
            full_name=user.full_name, username=user.username, telegram_id=str(user.id)
        )
        records = self.service.question_record.get_records_by_user(
            user_id=user_dict["id"],
            summary_type=summary_type,
            is_last_week=is_last_week,
        )
        if not records:
            await self._edit_query_text(
                context,
                query,
                "You did not complete any questions!",
                InlineKeyboardMarkup(self.__get_back_keyboard()),
            )
            return

        strftime_format = MONTH_ALL_SUMMARY_STRFTIME_FORMAT
        if summary_type == SummaryType.WEEKLY:
            strftime_format = WEEK_SUMMARY_STRFTIME_FORMAT
        if summary_type == SummaryType.ALL_UNIQUE:
            records.sort(
                key=lambda x: (
                    difficulty_to_int(x["difficulty"]),
                    platform_to_int(x["platform"]),
                )
            )

        header_text = (
            f"Questions you have completed {summary_type.format(is_last_week)}"
        )
        items = [
            f"{record['question_name']} [{record['difficulty'].title()}] [{format_platform_name(record['platform'])}]{'' if summary_type == SummaryType.ALL_UNIQUE else ' (' + record['created_at'].strftime(strftime_format) + ')'}"
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
