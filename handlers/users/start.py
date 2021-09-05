from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from keyboards.default.registation import reg
from loader import dp
from database.connect_db import conn, cur
from keyboards.default.worker_no_job import worker_no_job
from keyboards.default.worker_job import worker_start_job
from keyboards.inline.foreman_menu import foreman_menu
from states.worker import worker
from states.foreman import foreman
from keyboards.inline.worker import worker_menu
from keyboards.default.foreman_job import foreman_start_job
from loader import bot
from datetime import datetime
name_worker = ""
name_foreman = ""
st = ""
st_name_task = ""
@dp.message_handler(CommandStart())
async def show_menu(message: Message):
    try:
        for i in range(message.message_id - 1, 1, -1):
            print(i)
            await bot.delete_message(message.from_user.id, i)
    except:
        print(123)
        conn.commit()
        mes = message.from_user.id
        cur.execute("select fio, status, role, telegramidforeman from tabEmployer where telegramid=%s" % mes)
        a = cur.fetchall()
        if(a):
            if (a[0][1]=='Подтвержден'):
                if(a[0][2]=='Инженер'):
                    cur.execute("select object from tabEmployer where telegramid=%s" % mes)
                    obj = cur.fetchall()
                    if (obj[0][0]):
                        await message.answer('Вас приветствует персональный помощник "Цифрум" "! \nНажмите кнопку "Начать рабочий день", чтобы начать работу.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)', disable_web_page_preview=True, reply_markup=foreman_start_job)
                    else:
                        await message.answer('Добрый день! Вы не прикреплены к объекту.', reply_markup=foreman_start_job)
                elif(a[0][2]=='Рабочий'):
                    if(a[0][3] != None):
                        await message.answer('Вас приветствует персональный помощник "Цифрум" "! \nНажмите кнопку "Начать рабочий день", чтобы начать работу.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)', disable_web_page_preview=True, reply_markup=worker_start_job)
                    else:
                        await message.answer(f"Добрый день, у вас нет руководителя, нажмите на кнопку, чтобы проверить обновления.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)", disable_web_page_preview=True, reply_markup=worker_no_job)
                        await worker.no_job.set()
                elif(a[0][2]):
                    await message.answer("Добрый день, для вашей должности пока нет функционала.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)", disable_web_page_preview=True, reply_markup=ReplyKeyboardRemove())
                else:
                    await message.answer("Добрый день, вам ещё не назначили должность, напишите /start через некоторое время.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)", disable_web_page_preview=True, reply_markup=ReplyKeyboardRemove())
            elif(a[0][1]=='На рассмотрении'):
                await message.answer("Ваша заявка на регистрацию находится на рассмотрении, напишите /start через некоторое время.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)", disable_web_page_preview=True)
            elif(a[0][1]=='Не подтвержден'):
                await message.answer("Ваши данные регистрации не верны. Попробуйте зарегистрировать заново или свяжитесь с поддержкой.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)", disable_web_page_preview=True)
                cur.execute("delete from tabEmployer where telegramid=?", [mes])
                conn.commit()
            elif(a[0][1]=='Уволен'):
                await message.answer("Вы уволены.", reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer('Нажмите кнопку "Зарегистрироваться", чтобы пройти регистрацию.\n\nПосле подтверждения личности, вы можете начать работу!\n\n⚠️ Связаться с тех.поддержкой https://t.me/auxiliume \n\n📞 Либо позвоните по телефону +79994601211 (Игорь)', disable_web_page_preview=True,  reply_markup=reg)

@dp.message_handler(text="Начать рабочий день", state="*")
async def join_job(message: Message, state=FSMContext):
    await state.update_data(first_mes=message.message_id)
    data = await state.get_data("first_mes")
    print(data)
    try:
        for i in range(message.message_id - 1, 1, -1):
            print(i)
            await bot.delete_message(message.from_user.id, i)
    except:
        print("mes not found")
    print(123)
    conn.commit()
    mes = message.from_user.id
    cur.execute("select fio, status, role, telegramidforeman from tabEmployer where telegramid=%s" % mes)
    a = cur.fetchall()
    if (a):
        if (a[0][1] == 'Подтвержден'):
            if (a[0][2] == 'Инженер'):
                cur.execute("select object from tabEmployer where telegramid=%s" % mes)
                obj = cur.fetchall()
                if (obj[0][0]):
                    mesag = await message.answer('Добрый день!', reply_markup=ReplyKeyboardRemove())
                    print(mesag)
                    #await bot.delete_message(message.from_user.id, mesag.message_id)
                    await bot.send_message(message.from_user.id, text="Главное меню", reply_markup=foreman_menu)
                    await foreman.job.set()
                else:
                    await message.answer('Добрый день! Вы не прикреплены к объекту.', reply_markup=foreman_start_job)
            elif (a[0][2] == 'Рабочий'):
                if (a[0][3]):
                    cur.execute("update tabEmployer set activity=1 where name=?", [mes])
                    conn.commit()
                    mesag = await message.answer('Добрый день!', reply_markup=ReplyKeyboardRemove())
                    print(mesag)
                    #await bot.delete_message(message.from_user.id, mesag.message_id)
                    await bot.send_message(message.from_user.id, text="Главное меню", reply_markup=worker_menu)
                    await worker.job.set()
                else:
                    await message.answer("Добрый день, у вас нет руководителя, нажмите на кнопку, чтобы проверить обновления.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)", disable_web_page_preview=True,
                        reply_markup=worker_no_job)
                    await worker.no_job.set()
            elif (a[0][2]):
                await message.answer("Добрый день, для вашей должности пока нет функционала.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)", disable_web_page_preview=True,
                                     reply_markup=ReplyKeyboardRemove())
            else:
                await message.answer("Добрый день, вам ещё не назначили должность, напишите /start через некоторое время.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)", disable_web_page_preview=True, reply_markup=ReplyKeyboardRemove())
        elif (a[0][1] == 'На рассмотрении'):
            await message.answer(
                "Ваша заявка на регистрацию находится на рассмотрении, напишите /start через некоторое время.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)", disable_web_page_preview=True)
        elif (a[0][1] == 'Неверно введены данные'):
            await message.answer("Ваши данные регистрации не верны. Попробуйте зарегистрировать заново или свяжитесь с поддержкой.\n\n⚠️ Тех.поддержка https://t.me/auxiliume\n\n📞 Телефон тех. поддержки +79994601211 (Игорь)", disable_web_page_preview=True)
            cur.execute("delete from tabEmployer where telegramid=?", [mes])
            conn.commit()
        elif (a[0][1] == 'Уволен'):
            await message.answer("Вы уволены.", reply_markup=ReplyKeyboardRemove())
    else:
            await message.answer('Нажмите кнопку "Зарегистрироваться", чтобы пройти регистрацию.\n\nПосле подтверждения личности, вы можете начать работу!\n\n⚠️ Связаться с тех.поддержкой https://t.me/auxiliume \n\n📞 Либо позвоните по телефону +79994601211 (Игорь)', disable_web_page_preview=True, reply_markup=reg)

@dp.message_handler(text="/back", state="*")
async def back_from_reg(message: Message, state=FSMContext):
    await message.answer("Нажмите /start, чтобы возобновить работу с ботом", reply_markup=ReplyKeyboardRemove())
    await state.finish()

@dp.message_handler(text="отмена", state="*")
async def back_from_reg(message: Message, state=FSMContext):
    await message.answer("Нажмите /start, чтобы возобновить работу с ботом", reply_markup=ReplyKeyboardRemove())
    await state.finish()