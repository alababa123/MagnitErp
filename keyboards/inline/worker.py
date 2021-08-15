from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline.foreman_menu_callback import f_m
worker_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Заявки", callback_data=f_m.new(name="Сделать отчет")
            )
        ],
        [
            InlineKeyboardButton(text="История", callback_data=f_m.new(name="История")
            )
        ],
        [
            InlineKeyboardButton(text="Обновить меню", callback_data=f_m.new(name="Обновить меню")
            )
        ],
        [
            InlineKeyboardButton(text="Закончить рабочий день", callback_data=f_m.new(name="Закончить рабочий день")
            )
        ]
    ]
)