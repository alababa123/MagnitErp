from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from keyboards.inline.reg_buttons import end_reg
from keyboards.default.registation import reg
from loader import dp
from states.registration import registration as reg
from aiogram.dispatcher import FSMContext
from keyboards.default.cancel import cancel
from keyboards.default.start import start_keyboard
from data.config import loc_photo_worker, loc_pass_worker
#from database.connect_db import conn, cur
from datetime import datetime
import re
from utils.format import format_phone
from loader import bot
from data.config import example_photo
import mariadb
from data.config import user, password, host, port, database

mes = ''
@dp.message_handler(text="Зарегистрироваться", state=None)
async def enter_reg(message: Message):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    mes = message.from_user.id
    cur.execute("select telegramid from tabEmployer where telegramid=%d" %mes)
    a = cur.fetchall()
    if (a):
        await message.answer("Вы уже зарегистрированны, либо ваш аккаунт еще не подтвердили.", reply_markup=start_keyboard)
        conn.close()
    else:
        await message.answer("При желании вы всегда можете выйти в главное меню, нажав кнопку отмена", reply_markup=cancel)
        await message.answer("Введите ФИО")
        conn.close()
        await reg.fio.set()

@dp.message_handler(state=reg.fio)
async def reg_fio(message: Message, state: FSMContext):
    pattern = r'[а-яА-ЯёЁ]+'
    if re.match(pattern, message.text):
        fio = message.text
        markup = ReplyKeyboardMarkup(resize_keyboard=False).add(KeyboardButton('Нажмите по кнопке, чтобы отправить свой номер телефона', request_contact=True))
        await message.answer("Нажмите на кнопку, чтобы отправить свой номер телефона", reply_markup=markup)
        await state.update_data(fio=fio)
        await state.update_data(telegramid=message.from_user.id)
        await reg.phone.set()
    else:
        await message.answer("Невеный формат\nПожалуйста, вводите ФИО без цифр и только русскими буквами")
        await reg.fio.set()

@dp.message_handler(content_types=["contact"], state=reg.phone)
async def reg_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    pattern_abc = r'[а-яА-ЯёЁa-fA-F]+'
    pattern = r'(\+7|8).*?(\d{3}).*?(\d{3}).*?(\d{2}).*?(\d{2})'
    if (phone[0] == '8'):
        await message.answer("Отправьте страницу паспорта с вашим фото и ФИО, как показано на примере ниже", reply_markup=ReplyKeyboardRemove())
        await bot.send_photo(message.from_user.id, photo=open(example_photo, 'rb'))
        await state.update_data(phone=phone)
        await reg.passport.set()
    elif(phone[0] == '+'):
        await message.answer("Отправьте страницу паспорта с вашим фото и ФИО, как показано на примере ниже", reply_markup=ReplyKeyboardRemove())
        await bot.send_photo(message.from_user.id, photo=open(example_photo, 'rb'))
        await state.update_data(phone=phone)
        await reg.passport.set()
    elif(phone[0] == '7'):
        phone = "+" + phone
        await message.answer("Отправьте страницу паспорта с вашим фото и ФИО, как показано на примере ниже", reply_markup=ReplyKeyboardRemove())
        await bot.send_photo(message.from_user.id, photo=open(example_photo, 'rb'))
        await state.update_data(phone=phone)
        await reg.passport.set()
    else:
        await message.answer("Отправьте страницу паспорта с вашим фото и ФИО, как показано на примере ниже", reply_markup=ReplyKeyboardRemove())
        await bot.send_photo(message.from_user.id, photo=open(example_photo, 'rb'))
        await state.update_data(phone=phone)
        await reg.passport.set()
@dp.message_handler(state=reg.passport, content_types=['photo'])
async def reg_passport(message, state: FSMContext):
    passport = message.photo[-1]
    await passport.download(destination=loc_pass_worker + "passport_worker" + str(message.from_user.id) + ".jpg")
    await state.update_data(path_pas="/files/pass_worker/passport_worker" + str(message.from_user.id) + ".jpg")
    await message.answer("Отправьте вашу фотографию")
    data = await state.get_data()
    await reg.photo.set()

@dp.message_handler(state=reg.photo, content_types=['photo'])
async def reg_passport(message, state: FSMContext):
    passport = message.photo[-1]
    await passport.download(destination=loc_photo_worker + "photo_worker" + str(message.from_user.id) + ".jpg")
    await state.update_data(path_photo="/files/photo_worker/photo_worker" + str(message.from_user.id) + ".jpg")
    data = await state.get_data()
    await message.answer("Пожалуйста, проверте верна ли введеная информация\n" \
                         "ФИО: " + data.get("fio") + "\n"
                                                     "Номер телефона: " + data.get("phone") + "\n", reply_markup=end_reg)
    await reg.check.set()

@dp.callback_query_handler(text_contains="reg", state=reg.check)
async def reg_check(call: CallbackQuery, state: FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    now = datetime.now()
    callback_data = call.data
    data = await state.get_data()
    if callback_data == "reg:True":
        await call.message.answer("Ваша заявка отправлена на рассмотрение оператором, отправьте боту /start для проверки статуса вашего аккаунта.", reply_markup=ReplyKeyboardRemove())
        cur.execute("INSERT INTO tabEmployer (name ,creation ,owner ,fio ,phone_number ,telegramid ,photo_pass ,photo, status, telegramidforeman, amounttask, amountjob, rate, amounttask_now) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    [data.get("telegramid"), now, "Administrator", data.get("fio"), data.get("phone"),
                     data.get("telegramid"), data.get("path_pas"), data.get("path_photo"), "На рассмотрении", '', 0, 0, 0, 0])
        conn.commit()
        conn.close()
        await state.finish()
    else:
        await call.message.answer("Начнём сначала! Введите ФИО.\n")
        conn.close()
        await reg.fio.set()
