from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='\U0001f4ca \u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430', callback_data='adm_stats'),
            ],
            [
                InlineKeyboardButton(text='\U0001f4cb Premium \u0441\u043f\u0438\u0441\u043e\u043a', callback_data='adm_prem_list'),
            ],
            [
                InlineKeyboardButton(text='\u2753 \u041f\u043e\u043c\u043e\u0449\u044c \u043f\u043e \u043a\u043e\u043c\u0430\u043d\u0434\u0430\u043c', callback_data='adm_help'),
            ],
            [
                InlineKeyboardButton(text='\U0001f3e0 \u0412 \u043c\u0435\u043d\u044e', callback_data='back_to_menu'),
            ],
        ]
    )
