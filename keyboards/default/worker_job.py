from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

worker_start_job = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Начать рабочий день"),
        ],
        [
            KeyboardButton(text="Заявки"),
        ],
    ],
    resize_keyboard=True
)

