from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text='\U0001f5bc \u0413\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044f \u043a\u0430\u0440\u0442\u0438\u043d\u043e\u043a'), KeyboardButton(text='\U0001f4dd \u0413\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044f \u0442\u0435\u043a\u0441\u0442\u0430')],
        [KeyboardButton(text='\U0001f4ac \u0427\u0430\u0442 \u0441 \u0418\u0418'), KeyboardButton(text='\U0001f50a \u041e\u0437\u0432\u0443\u0447\u043a\u0430 \u0442\u0435\u043a\u0441\u0442\u0430')],
        [KeyboardButton(text='\U0001f3a4 \u0420\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u0432\u0430\u043d\u0438\u0435 \u0433\u043e\u043b\u043e\u0441\u0430'), KeyboardButton(text='\U0001f48e \u041a\u0443\u043f\u0438\u0442\u044c Premium')],
        [KeyboardButton(text='\U0001f464 \u041c\u043e\u0439 \u043f\u0440\u043e\u0444\u0438\u043b\u044c'), KeyboardButton(text='\u2139\ufe0f \u041f\u043e\u043c\u043e\u0449\u044c')],
    ]
    if is_admin:
        rows.append([KeyboardButton(text='\U0001f6e0 \u0410\u0434\u043c\u0438\u043d-\u043f\u0430\u043d\u0435\u043b\u044c')])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder='\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435\u2026',
    )


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='\U0001f3e0 \u0412 \u043c\u0435\u043d\u044e', callback_data='back_to_menu')]]
    )


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='\u274c \u041e\u0442\u043c\u0435\u043d\u0430', callback_data='cancel')]]
    )


def premium_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='\u2b50 \u041e\u043f\u043b\u0430\u0442\u0438\u0442\u044c 100 Stars', callback_data='buy_premium')],
            [InlineKeyboardButton(text='\U0001f3e0 \u0412 \u043c\u0435\u043d\u044e', callback_data='back_to_menu')],
        ]
    )
