from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from ..utils import UUID_REGEX, unwrap
from .base import BaseHandler


class PaginationHandler(BaseHandler):
    def bind(self, app: Application) -> None:
        app.add_handler(CallbackQueryHandler(self.paginate, f"^{UUID_REGEX}_\d+$"))

    async def paginate(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = await self._get_and_answer_query(update)
        query.data = unwrap(query.data)
        query.message = unwrap(query.message)
        query.message.text = unwrap(query.message.text)

        id, page = query.data.split("_")
        pagination_data = self.helper.pagination.get_data(id)
        if pagination_data is None:
            await self._edit_query_text(
                context,
                query,
                "(The data shown here has since expired)\n\n" + query.message.text,
            )
            return

        message, keyboard = pagination_data.generate_message(int(page))
        await self._edit_query_text(context, query, message, keyboard)
