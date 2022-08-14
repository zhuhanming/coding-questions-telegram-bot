from math import ceil
from typing import Callable, cast
from uuid import uuid4

from expiringdict import ExpiringDict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class PaginationData:
    def __init__(
        self,
        id: str,  # UUID4
        header_text: str,
        items: list[str],
        num_items_per_page: int = 10,
        # The second argument passed in is a zero-based index.
        item_to_button_generator: Callable[[str, int], InlineKeyboardButton]
        | None = None,
        other_buttons: list[list[InlineKeyboardButton]] = [],
    ):
        self.id = id
        self.header_text = header_text
        self.items = items
        self.num_items_per_page = num_items_per_page
        self.item_to_button_generator = item_to_button_generator
        self.other_buttons = other_buttons
        self.total_pages = ceil(len(self.items) / num_items_per_page)

    # TODO: Bold the headers
    def generate_message(self, page: int) -> tuple[str, InlineKeyboardMarkup]:
        """The page number is a zero-based index."""
        buttons = []
        page_buttons = []
        if 1 < self.total_pages <= 5:
            for i in range(self.total_pages):
                page_buttons.append(
                    InlineKeyboardButton(
                        text=f"· {i + 1} ·" if i == page else f"{i + 1}",
                        callback_data=f"{self.id}_{i}",
                    )
                )
        elif self.total_pages > 5:
            if page <= 2:
                for i in range(3):
                    page_buttons.append(
                        InlineKeyboardButton(
                            text=f"· {i + 1} ·" if i == page else f"{i + 1}",
                            callback_data=f"{self.id}_{i}",
                        )
                    )
                page_buttons.append(
                    InlineKeyboardButton(text="4 ›", callback_data=f"{self.id}_3")
                )
                page_buttons.append(
                    InlineKeyboardButton(
                        text=f"{self.total_pages} »",
                        callback_data=f"{self.id}_{self.total_pages - 1}",
                    )
                )
            elif page >= self.total_pages - 3:
                page_buttons.append(
                    InlineKeyboardButton(text="« 1", callback_data=f"{self.id}_0")
                )
                page_buttons.append(
                    InlineKeyboardButton(
                        text=f"‹ {self.total_pages - 3}",
                        callback_data=f"{self.id}_{self.total_pages - 4}",
                    )
                )
                for i in range(2, -1, -1):
                    page_buttons.append(
                        InlineKeyboardButton(
                            text=f"· {self.total_pages - i} ·"
                            if self.total_pages - i - 1 == page
                            else f"{self.total_pages - i}",
                            callback_data=f"{self.id}_{self.total_pages - i - 1}",
                        )
                    )
            else:
                page_buttons.append(
                    InlineKeyboardButton(text="« 1", callback_data=f"{self.id}_0")
                )
                page_buttons.append(
                    InlineKeyboardButton(
                        text=f"‹ {page}", callback_data=f"{self.id}_{page - 1}"
                    )
                )
                page_buttons.append(
                    InlineKeyboardButton(
                        text=f"· {page + 1} ·", callback_data=f"{self.id}_{page}"
                    )
                )
                page_buttons.append(
                    InlineKeyboardButton(
                        text=f"{page + 2} ›", callback_data=f"{self.id}_{page + 1}"
                    )
                )
                page_buttons.append(
                    InlineKeyboardButton(
                        text=f"{self.total_pages} »",
                        callback_data=f"{self.id}_{self.total_pages - 1}",
                    )
                )
        if page_buttons:
            buttons.append(page_buttons)

        full_header = self.header_text
        if self.total_pages > 1:
            full_header += f" ({page + 1}/{self.total_pages})"
        message_parts = [f"{full_header}:\n\n"]

        for i in range(
            page * self.num_items_per_page,
            min((page + 1) * self.num_items_per_page, len(self.items)),
        ):
            message_parts.append(f"{i + 1}. {self.items[i]}\n")
            if self.item_to_button_generator is not None:
                buttons.append([self.item_to_button_generator(self.items[i], i)])

        full_message = "".join(message_parts).strip()
        buttons.extend(self.other_buttons)

        return full_message, InlineKeyboardMarkup(buttons)


class PaginationHelper:
    def __init__(self):
        # Cache 1000 items for up to 1 day each.
        self.cache = ExpiringDict(1000, 86400)

    def create_and_set_data(
        self,
        header_text: str,
        items: list[str],
        num_items_per_page: int = 10,
        item_to_button_generator: Callable[[str, int], InlineKeyboardButton]
        | None = None,
        other_buttons: list[list[InlineKeyboardButton]] = [],
    ) -> PaginationData:
        id = str(uuid4())
        pagination = PaginationData(
            id,
            header_text,
            items,
            num_items_per_page,
            item_to_button_generator,
            other_buttons,
        )
        self.cache[pagination.id] = pagination
        return pagination

    def get_data(self, pagination_id: str) -> PaginationData | None:
        return cast(PaginationData | None, self.cache.get(pagination_id, None))
