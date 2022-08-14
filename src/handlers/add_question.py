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
from ..utils import InvalidUserDataException, unwrap
from .base import BaseHandler

FETCH, MANUAL_NAME, MANUAL_DIFFICULTY_PRE, MANUAL_DIFFICULTY, THANKS = range(5)


class AddQuestionHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(
            ConversationHandler(
                entry_points=[CallbackQueryHandler(self.add_question, "add_question")],
                states={
                    FETCH: [
                        MessageHandler(
                            filters.TEXT & ~filters.COMMAND, self.try_fetch_details
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

    async def add_question(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
        query = unwrap(update.callback_query)
        user = unwrap(update.effective_user)
        await query.answer()

        await query.edit_message_text(
            f"Hi {user.full_name}! Glad to see that you've been working hard!\n"
            "Can you send me the URL of the question that you've attempted?",
            reply_markup=InlineKeyboardMarkup(self.__get_cancel_keyboard()),
        )
        return FETCH

    async def try_fetch_details(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        update.message = unwrap(update.message)
        update.message.text = unwrap(update.message.text)
        if context.user_data is None:
            raise InvalidUserDataException()

        url = update.message.text.lower()
        platform = "other"
        if bool(match(LEETCODE_REGEX, url)):
            platform = "leetcode"
        elif bool(match(HACKERRANK_REGEX, url)):
            platform = "hackerrank"
        context.user_data["PLATFORM"] = platform

        if platform == "other":
            await update.message.reply_text(
                "I was unable to fetch the question details from your URL.\n"
                "Do you mind letting me know what the name of the question you attempted was?\n",
                reply_markup=InlineKeyboardMarkup(self.__get_cancel_keyboard()),
            )
            return MANUAL_NAME

        is_leetcode = platform == "leetcode"
        message = await update.message.reply_text(
            "This part may take a while to load.\n" "Do be patient with me!"
        )
        question_info = self.helper.question.get_question_info(
            url=url, is_leetcode=is_leetcode
        )
        context.user_data["QUESTION_NAME"] = question_info.name
        context.user_data["QUESTION_DIFFICULTY"] = (
            question_info.difficulty.lower()
            if question_info.difficulty is not None
            else None
        )

        if question_info.name is None:
            await message.edit_text(
                "It seems like either the URL is invalid or you sent me a premium question!\n"
                "Please enter the name of the question manually.",
                reply_markup=InlineKeyboardMarkup(self.__get_cancel_keyboard()),
            )
            return MANUAL_NAME

        if question_info.difficulty is None:
            await message.edit_text(
                "I tried my best to get the question title either from the website or from the URL you gave!\n"
                f"Is your question title: {question_info.name}?",
                reply_markup=InlineKeyboardMarkup(self.__get_confirmation_keyboard()),
            )
            return MANUAL_DIFFICULTY_PRE

        assert question_info.name is not None
        assert question_info.difficulty is not None

        await message.edit_text(
            "I managed to find the question info from the website directly!\n"
            f"Is your question: {question_info.name} [{question_info.difficulty.title()}]?",
            reply_markup=InlineKeyboardMarkup(self.__get_confirmation_keyboard()),
        )
        return THANKS

    async def manual_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        update.message = unwrap(update.message)
        update.message.text = unwrap(update.message.text)
        if context.user_data is None:
            raise InvalidUserDataException()

        question_name = update.message.text
        context.user_data["QUESTION_NAME"] = question_name

        await update.message.reply_text(
            "What is the difficulty of your question?",
            reply_markup=InlineKeyboardMarkup(self.__get_difficulty_keyboard()),
        )
        return MANUAL_DIFFICULTY

    async def manual_difficulty_pre(
        self, update: Update, _: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = unwrap(update.callback_query)
        await query.answer()

        if query.data == "no":
            await query.edit_message_text(
                "Sorry that I got your question title wrong!\n"
                "Do you mind sending the name of the question here?"
            )
            return MANUAL_NAME

        await query.edit_message_text(
            "Awesome! What is the difficulty of the question?",
            reply_markup=InlineKeyboardMarkup(self.__get_difficulty_keyboard()),
        )
        return MANUAL_DIFFICULTY

    async def manual_difficulty(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = unwrap(update.callback_query)
        if context.user_data is None:
            raise InvalidUserDataException()

        question_difficulty = query.data
        context.user_data["QUESTION_DIFFICULTY"] = question_difficulty
        question_name = context.user_data["QUESTION_NAME"]

        assert question_name is not None
        assert question_difficulty is not None

        await query.edit_message_text(
            f"Just to confirm, is your question: {question_name} [{question_difficulty.title()}]?",
            reply_markup=InlineKeyboardMarkup(self.__get_confirmation_keyboard()),
        )
        return THANKS

    async def thanks(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = unwrap(update.callback_query)
        user = unwrap(update.effective_user)
        if context.user_data is None:
            raise InvalidUserDataException()

        if query.data == "no":
            await query.edit_message_text(
                "Sorry that I got your question details wrong!\n"
                "Do you mind sending the name of the question here?"
            )
            return MANUAL_NAME

        platform = context.user_data.get("PLATFORM")
        question_name = context.user_data.get("QUESTION_NAME")
        difficulty = context.user_data.get("QUESTION_DIFFICULTY")

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

        context.user_data.clear()
        await query.edit_message_text(
            "Awesome! Good job with the question!\n" "How else can I help you?",
            reply_markup=InlineKeyboardMarkup(self.__get_final_keyboard()),
        )
        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = unwrap(update.callback_query)
        if context.user_data is None:
            raise InvalidUserDataException()

        await query.edit_message_text(
            "No worries! Feel free to add a question when you're ready!",
            reply_markup=InlineKeyboardMarkup(self.__get_final_keyboard()),
        )

        context.user_data.clear()
        return ConversationHandler.END

    def __get_cancel_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return [[InlineKeyboardButton(text="Cancel", callback_data="cancel")]]

    def __get_confirmation_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return [
            [
                InlineKeyboardButton(text="Yes", callback_data="yes"),
                InlineKeyboardButton(text="No", callback_data="no"),
            ]
        ]

    def __get_difficulty_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return [
            [InlineKeyboardButton(text="Easy", callback_data="easy")],
            [InlineKeyboardButton(text="Medium", callback_data="medium")],
            [InlineKeyboardButton(text="Hard", callback_data="hard")],
        ]

    def __get_final_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return [
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
