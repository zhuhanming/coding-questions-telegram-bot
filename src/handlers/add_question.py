from re import match

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ..helpers import HACKERRANK_REGEX, LEETCODE_REGEX
from .base import BaseHandler

FETCH, MANUAL_NAME, MANUAL_DIFFICULTY_PRE, MANUAL_DIFFICULTY, THANKS = range(5)

# TODO: Add comments to code
class AddQuestionHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(
            ConversationHandler(
                entry_points=[CallbackQueryHandler(self.add_question, "add_question")],
                states={
                    FETCH: [
                        MessageHandler(
                            filters.TEXT & ~filters.COMMAND, self.try_fetch_question
                        )
                    ],
                    MANUAL_NAME: [
                        MessageHandler(
                            filters.TEXT & ~filters.COMMAND, self.manual_name
                        )
                    ],
                    MANUAL_DIFFICULTY_PRE: [
                        CallbackQueryHandler(self.manual_difficulty_pre, "^(yes|no)$")
                    ],
                    MANUAL_DIFFICULTY: [
                        CallbackQueryHandler(
                            self.manual_difficulty, "^(easy|medium|hard)$"
                        )
                    ],
                    THANKS: [CallbackQueryHandler(self.thanks, "^(yes|no)$")],
                },
                fallbacks=[CallbackQueryHandler(self.cancel, "cancel")],
            )
        )

    async def add_question(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = await self._get_and_answer_query(update)
        await self._edit_query_text(
            context,
            query,
            f"Hi {self._get_user(update).full_name}! Glad to see that you've been working hard!\n"
            "Can you send me the URL of the question that you've attempted?",
            self.__get_cancel_keyboard(),
        )
        return FETCH

    async def try_fetch_question(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        await self._clear_previous_message_reply_markup(update, context)
        original_message = self._get_message(update)

        url = self._get_message_text(update).lower()
        platform = "other"
        if bool(match(LEETCODE_REGEX, url)):
            platform = "leetcode"
        elif bool(match(HACKERRANK_REGEX, url)):
            platform = "hackerrank"
        self._set_context_value(context, "PLATFORM", platform)

        if platform == "other":
            await self._reply_text(
                context,
                original_message,
                "I was unable to fetch the question details from your URL.\n\n"
                "Do you mind letting me know what the name of the question you attempted was?\n",
                self.__get_cancel_keyboard(),
            )
            return MANUAL_NAME

        is_leetcode = platform == "leetcode"
        message = await self._reply_text(
            context,
            original_message,
            "This part may take a while to load.\n" "Do be patient with me!",
        )
        question_info = self.helper.question.get_question_info(
            url=url, is_leetcode=is_leetcode
        )
        self._set_context_value(context, "QUESTION_NAME", question_info.name)
        self._set_context_value(
            context,
            "QUESTION_DIFFICULTY",
            question_info.difficulty.lower()
            if question_info.difficulty is not None
            else None,
        )

        if question_info.name is None:
            await self._edit_message_text(
                context,
                message,
                "It seems like either the URL is invalid or you sent me a premium question!\n\n"
                "Please enter the name of the question manually.",
                self.__get_cancel_keyboard(),
            )
            return MANUAL_NAME

        if question_info.difficulty is None:
            await self._edit_message_text(
                context,
                message,
                "I tried my best to get the question title either from the website or from the URL you gave!\n\n"
                f"Is your question title: {question_info.name}?",
                self.__get_confirmation_keyboard(),
            )
            return MANUAL_DIFFICULTY_PRE

        await self._edit_message_text(
            context,
            message,
            "I managed to find the question info from the website directly!\n\n"
            f"Is your question: {question_info.name} [{question_info.difficulty.title()}]?",
            self.__get_confirmation_keyboard(),
        )
        return THANKS

    async def manual_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        await self._clear_previous_message_reply_markup(update, context)
        self._set_context_value(
            context, "QUESTION_NAME", self._get_message_text(update)
        )
        await self._reply_text(
            context,
            self._get_message(update),
            "What is the difficulty of your question?",
            self.__get_difficulty_keyboard(),
        )
        return MANUAL_DIFFICULTY

    async def manual_difficulty_pre(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = await self._get_and_answer_query(update)
        if query.data == "no":
            await self._edit_query_text(
                context,
                query,
                "Sorry that I got your question title wrong!\n\n"
                "Do you mind sending the name of the question here?",
                self.__get_cancel_keyboard(),
            )
            return MANUAL_NAME

        await self._edit_query_text(
            context,
            query,
            "Awesome! What is the difficulty of the question?",
            self.__get_difficulty_keyboard(),
        )
        return MANUAL_DIFFICULTY

    async def manual_difficulty(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = await self._get_and_answer_query(update)
        question_difficulty = str(query.data)
        self._set_context_value(context, "QUESTION_DIFFICULTY", question_difficulty)
        question_name = self._get_context_value(context, "QUESTION_NAME")
        await self._edit_query_text(
            context,
            query,
            f"Just to confirm, is your question: {question_name} [{question_difficulty.title()}]?",
            self.__get_confirmation_keyboard(),
        )
        return THANKS

    async def thanks(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = await self._get_and_answer_query(update)
        if query.data == "no":
            await self._edit_query_text(
                context,
                query,
                "Sorry that I got your question details wrong!\n"
                "Do you mind sending the name of the question here?",
                self.__get_cancel_keyboard(),
            )
            return MANUAL_NAME

        platform = self._get_context_value(context, "PLATFORM")
        question_name = self._get_context_value(context, "QUESTION_NAME")
        difficulty = self._get_context_value(context, "QUESTION_DIFFICULTY")

        user = self._get_user(update)
        # Persist data to database
        user_dict = self.service.user.create_if_not_exists(
            full_name=user.full_name, telegram_id=str(user.id)
        )
        self.service.question_record.create_question_record(
            user_id=user_dict["id"],
            platform=platform,
            question_name=question_name,
            difficulty=difficulty,
        )

        self.helper.logger.info(
            "User %s added question: %s [%s] [%s]",
            user_dict["full_name"],
            question_name,
            platform,
            difficulty,
        )

        # TODO: Show some meaningful summary of data at this point
        self._clear_context_values(context)
        await self._edit_query_text(
            context,
            query,
            "Awesome! Good job with the question!\n\n" "How else can I help you?",
            self.__get_final_keyboard(),
        )
        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = await self._get_and_answer_query(update)
        await self._edit_query_text(
            context,
            query,
            "No worries! Feel free to add another question when you're ready!\n\n"
            "How else can I help you?",
            self.__get_final_keyboard(),
        )
        self._clear_context_values(context)
        return ConversationHandler.END

    def __get_cancel_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Cancel", callback_data="cancel")]]
        )

    def __get_confirmation_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="Yes", callback_data="yes"),
                    InlineKeyboardButton(text="No", callback_data="no"),
                ]
            ]
        )

    def __get_difficulty_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(text="Easy", callback_data="easy")],
                [InlineKeyboardButton(text="Medium", callback_data="medium")],
                [InlineKeyboardButton(text="Hard", callback_data="hard")],
            ]
        )

    def __get_final_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Add another question", callback_data="add_question"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Complete an interview", callback_data="complete_interview"
                    )
                ],
                [InlineKeyboardButton(text="View stats", callback_data="view_stats")],
            ]
        )
