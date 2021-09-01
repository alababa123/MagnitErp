from datetime import time
import os.path
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from loader import dp, bot
from aiogram.dispatcher import FSMContext
from database.connect_db import conn, cur, cur1
import datetime
from keyboards.default.worker_job import worker_start_job
from states.worker import worker
from keyboards.inline.worker import worker_menu
from keyboards.default.worker_no_job import worker_no_job
import re
subject_task = ""
parent_task = ""
@dp.message_handler(text="Заявки", state=None)
async def claim(message:Message, state=FSMContext):
    conn.commit()
    tgid = message.from_user.id
    cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        conn.commit()
        cur.execute("select name, subject from tabTask where workerID=? and progress < 100", [tgid])
        section_task = cur.fetchall()
        free_work = []
        for i in section_task:
            free_work.append([InlineKeyboardButton(text=i[1], callback_data=i[0])])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await message.answer(text="Заявки", reply_markup=foreman_btn)
        await worker.zayavki.set()
@dp.message_handler(text="Заявки", state=worker.zayavki)
async def claim(message:Message, state=FSMContext):
    conn.commit()
    tgid = message.from_user.id
    cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        conn.commit()
        cur.execute("select name, subject from tabTask where workerID=? and progress < 100", [tgid])
        section_task = cur.fetchall()
        free_work = []
        for i in section_task:
            free_work.append([InlineKeyboardButton(text=i[1], callback_data=i[0])])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await message.answer(text="Заявки", reply_markup=foreman_btn)
        await worker.zayavki.set()
@dp.callback_query_handler(state=worker.zayavki)
async def zayavki(call: CallbackQuery, state=FSMContext):
    conn.commit()
    tgid = call.from_user.id
    cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await call.message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        conn.commit()
        call_data = call.data
        cur.execute("update tabTask set perfomance=1 where name=?", [call_data])
        conn.commit()
        cur.execute("select subject, description, status, exp_start_date, exp_end_date, expected_time from tabTask where name='%s'" % call_data)
        task_subject = cur.fetchall()
        await state.update_data(task_name=call_data, task_subject=task_subject[0][0])
        free_work = []
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Задача: %s "
                                          "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                          "Подробности задачи: %s "
                                          "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                          "Дата начала: %s\n"
                                          "Дата окончания: %s"
                                          "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                          "Ожидаемое время выполнения: %s часа(-ов)"
                                          "\n➖➖➖➖➖➖➖➖➖➖➖\n" % (
                                          task_subject[0][0], task_subject[0][1], task_subject[0][3],
                                          task_subject[0][4], task_subject[0][5]), reply_markup=foreman_btn)
        await worker.zayavki_back.set()
@dp.callback_query_handler(state=worker.zayavki_back)
async def back(call: CallbackQuery, state=FSMContext):
    conn.commit()
    tgid = call.from_user.id
    cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await call.message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        conn.commit()
        call_data = call.data
        if (call_data == "Назад"):
            conn.commit()
            cur.execute("select name, subject from tabTask where workerID=? and progress < 100", [call.from_user.id])
            section_task = cur.fetchall()
            free_work = []
            for i in section_task:
                free_work.append([InlineKeyboardButton(text=i[1], callback_data=i[0])])
            foreman_btn = InlineKeyboardMarkup(
                inline_keyboard=free_work,
            )
            await call.message.edit_text(text="Заявки", reply_markup=foreman_btn)
            await worker.zayavki.set()

@dp.message_handler(state=worker.start_job)
async def join_session(message: Message, state=FSMContext):
    tgid = message.from_user.id
    cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if(not name):
        await message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        cur.execute("select fio, telegramidforeman, foreman, object, phone_number")
        await state.update_data(telegramid=tgid, name_worker=name[0][0], name_foreman=name[0][2], telegramidforeman=name[0][1], object=name[0][3], phone_number=name[0][4])
        cur.execute("select phone_number from tabEmployer where telegramid=%s" %name[0][1])
        a = cur.fetchall()
        await state.update_data(phone_number_foreman=a[0][0])
        now = datetime.datetime.now().strftime("%A")
        await message.answer("Добрый день, сегодня %s число." %now, reply_markup=worker_menu)
        await worker.job.set()

@dp.callback_query_handler(text_contains="serv:История", state=worker.job)
async def work(call: CallbackQuery, state=FSMContext):
    cur.execute("select amounttask, amounttask_month, amounttask_cancel, amounttask_now, amounttask_cancel_now from tabEmployer where name=?", [call.from_user.id])
    tasks = cur.fetchall()
    free_work = []
    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(
        inline_keyboard=free_work,
    )
    await call.message.edit_text("Сделано всего: %s\n"
                                "Сделано за последний месяц: %s\n"
                                "Из них просрочено: %s"
                                "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                "Текущие поставленные: %s\n"
                                "Текущие просроченные: %s"
                                "\n➖➖➖➖➖➖➖➖➖➖➖\n" %(tasks[0][0], tasks[0][1], tasks[0][2],
                                                              tasks[0][3], tasks[0][4]), reply_markup=foreman_btn)
    await worker.info.set()

@dp.callback_query_handler(state=worker.info)
async def work(call: CallbackQuery, state=FSMContext):
    call_ = call.data
    if(call_ == "Назад"):
        await call.message.edit_text("Главное меню", reply_markup=worker_menu)
        await worker.job.set()

@dp.callback_query_handler(text_contains="serv:Обновить меню", state=worker.job)
async def work(call: CallbackQuery, state=FSMContext):
    await call.message.delete()
    await call.message.answer("Главное меню", reply_markup=worker_menu)
    await worker.job.set()

@dp.callback_query_handler(text_contains="serv:Сделать отчет", state=worker.job)
async def work(call: CallbackQuery, state=FSMContext):
    conn.commit()
    tgid = call.from_user.id
    cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await call.message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        conn.commit()
        cur.execute("select name, subject, status from tabTask where workerID=? and progress < 100", [call.from_user.id])
        section_task = cur.fetchall()
        free_work = []
        for i in section_task:
            print(i[2])
            if(i[2]=='Report'):
                free_work.append([InlineKeyboardButton(text="⚠ "+ str(i[1]), callback_data=i[0])])
            elif(i[2]=='Cancelled'):
                free_work.append([InlineKeyboardButton(text="❌ "+ str(i[1]), callback_data=i[0])])
            else:
                free_work.append([InlineKeyboardButton(text=i[1], callback_data=i[0])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Заявки", reply_markup=foreman_btn)
        await worker.section_task.set()

@dp.callback_query_handler(state=worker.section_task)
async def work(call: CallbackQuery, state=FSMContext):
    conn.commit()
    tgid = call.from_user.id
    cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await call.message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        conn.commit()
        call_data = call.data
        if (call_data == "Назад"):
            await call.message.edit_text("Главное меню", reply_markup=worker_menu)
            await worker.job.set()
        else:
            cur.execute("select subject, description, status, exp_start_date, exp_end_date, expected_time, comment_foreman, date_perfomance from tabTask where name='%s'" %call_data)
            task_subject = cur.fetchall()
            if(task_subject[0][7] =='' or task_subject[0][7] == None):
                cur.execute("update tabTask set perfomance=1, date_perfomance=? where name=?", [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), call_data])
            await state.update_data(task_name=call_data, task_subject=task_subject[0][0])
            free_work = []
            cur.execute("update tabTask set perfomance=1 where name=?", [call_data])
            conn.commit()
            if(task_subject[0][2] == "Working" or task_subject[0][2] == 'Report' or task_subject[0][2] == 'Cancelled'):
                free_work.append([InlineKeyboardButton(text="На исполнении ✅", callback_data="На исполнении ✅")])
                free_work.append([InlineKeyboardButton(text="Сделать отчет", callback_data="Отчет")])
                free_work.append([InlineKeyboardButton(text="Сдвинуть сроки", callback_data="Сдвинуть сроки")])
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            else:
                free_work.append([InlineKeyboardButton(text="На исполнении", callback_data="На исполнении")])
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(
                inline_keyboard=free_work,
            )
            if(task_subject[0][6]):
                await call.message.edit_text(text="Задача: %s "
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Подробности задачи: %s "
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Дата начала: %s\n"
                                                  "Дата окончания: %s"
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Ожидаемое время выполнения: %s часа(-ов)"
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Комментарий по отчету: %s"
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n" %(task_subject[0][0], task_subject[0][1], task_subject[0][3], task_subject[0][4], task_subject[0][5], task_subject[0][6]), reply_markup=foreman_btn)
            else:
                await call.message.edit_text(text="Задача: %s "
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Подробности задачи: %s "
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Дата начала: %s\n"
                                                  "Дата окончания: %s"
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Ожидаемое время выполнения: %s часа(-ов)"
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n" % (task_subject[0][0], task_subject[0][1], task_subject[0][3], task_subject[0][4], task_subject[0][5]), reply_markup=foreman_btn)
            await worker.task_profile.set()

@dp.callback_query_handler(state=worker.task_profile)
async def free_work(call: CallbackQuery, state=FSMContext):
    conn.commit()
    tgid = call.from_user.id
    cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await call.message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        call_data = call.data
        if(call_data == "На исполнении"):
            data = await state.get_data()
            cur.execute("update tabTask set status='Working', perfomance=1, date_progress=? where name=?", [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data.get("task_name")])
            conn.commit()
            task_name = data.get("task_name")
            await call.message.delete()
            await call.message.answer("Задача принята к исполнению!")
            cur.execute("select subject, description, status, exp_start_date, exp_end_date, expected_time, comment_foreman from tabTask where name='%s'" % data.get("task_name"))
            task_subject = cur.fetchall()
            cur.execute("select amounttask_now from tabEmployer where name=?", [call.from_user.id])
            amounttask_now = cur.fetchall()
            cur.execute("update tabEmployer set amounttask_now=? where name=?", [int(amounttask_now[0][0]) + 1, tgid])
            conn.commit()
            await state.update_data(task_name=call_data, task_subject=task_subject[0][0])
            free_work = []
            if (task_subject[0][2] == "Working" or task_subject[0][2] == 'Report' or task_subject[0][2] == 'Cancelled'):
                free_work.append([InlineKeyboardButton(text="На исполнении ✅", callback_data="На исполнении ✅")])
                free_work.append([InlineKeyboardButton(text="Сделать отчет", callback_data="Отчет")])
                free_work.append([InlineKeyboardButton(text="Сдвинуть сроки", callback_data="Сдвинуть сроки")])
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            else:
                free_work.append([InlineKeyboardButton(text="На исполнении", callback_data="На исполнении")])
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(
                inline_keyboard=free_work,
            )
            if (task_subject[0][6]):
                await call.message.answer(text="Задача: %s "
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Подробности задачи: %s "
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Дата начала: %s\n"
                                                  "Дата окончания: %s"
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Ожидаемое время выполнения: %s часа(-ов)"
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Комментарий по отчету: %s"
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n" % (
                                                  task_subject[0][0], task_subject[0][1], task_subject[0][3],
                                                  task_subject[0][4], task_subject[0][5], task_subject[0][6]),
                                             reply_markup=foreman_btn)
            else:
                await call.message.answer(text="Задача: %s "
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Подробности задачи: %s "
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Дата начала: %s\n"
                                                  "Дата окончания: %s"
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                                  "Ожидаемое время выполнения: %s часа(-ов)"
                                                  "\n➖➖➖➖➖➖➖➖➖➖➖\n" % (
                                                  task_subject[0][0], task_subject[0][1], task_subject[0][3],
                                                  task_subject[0][4], task_subject[0][5]), reply_markup=foreman_btn)
            await state.update_data(task_name=task_name)
            await worker.task_profile.set()
        elif(call_data == "Отчет"):
            await call.message.edit_text("Введите ваш отчет")
            await worker.input_task.set()
        elif(call_data == "Сдвинуть сроки"):
            await call.message.edit_text("Введите число на сколько дней увеличить срок?")
            await worker.shift_deadlines.set()
        else:
            conn.commit()
            cur.execute("select name, subject, status from tabTask where workerID=? and progress < 100",
                        [call.from_user.id])
            section_task = cur.fetchall()
            free_work = []
            for i in section_task:
                if (i[2] == 'Report'):
                    free_work.append([InlineKeyboardButton(text="⚠ " + str(i[1]), callback_data=i[0])])
                elif (i[2] == 'Cancelled'):
                    free_work.append([InlineKeyboardButton(text="❌ " + str(i[1]), callback_data=i[0])])
                else:
                    free_work.append([InlineKeyboardButton(text=i[1], callback_data=i[0])])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(
                inline_keyboard=free_work,
            )
            await call.message.edit_text(text="Заявки", reply_markup=foreman_btn)
            await worker.section_task.set()

@dp.message_handler(state=worker.shift_deadlines)
async def dead(message: Message, state=FSMContext):
    mes = message.text
    pattern_abc = r'[а-яА-ЯёЁa-fA-F+-]'
    if(re.search(pattern_abc, mes)):
        await message.answer("Число дней должно быть целым числом! Введите заново.")
        await worker.shift_deadlines.set()
    else:
        if(int(mes) <= 0 ):
            await message.answer("Число дней должно быть положительным числом! Введите заново.")
            await worker.shift_deadlines.set()
        else:
            await state.update_data(dealine_time=mes)
            await message.answer("Укажите причину")
            await worker.shift_deadlines_cause.set()
@dp.message_handler(state=worker.shift_deadlines_cause)
async def cause(message: Message, state=FSMContext):
    mes = message.text
    data = await state.get_data()
    name = str(data.get("task_name")) + str(message.from_user.id) + str(datetime.datetime.now().strftime("%H:%M:%S"))
    cur.execute("insert into tabshift_deadlines (name ,creation ,owner, days, cause, worker, task, status) values (?, ?, ?, ?, ?, ?, ?, ?)", [name, datetime.datetime.now(), "Administrator", data.get("dealine_time"), mes, message.from_user.id, data.get("task_name"), 'На рассмотрении'])
    conn.commit()
    cur.execute("select subject, exp_start_date, exp_end_date from tabTask where name=?", [data.get("task_name")])
    task_subj = cur.fetchall()
    cur.execute("select fio, phone_number, telegramidforeman from tabEmployer where name=?", [message.from_user.id])
    foremanid = cur.fetchall()
    await message.answer("Ваш запрос отправлен на подтверждение Инженеру")
    btn = []
    btn.append([InlineKeyboardButton(text="Одобрить", callback_data="Shift_Одобрить_%s" %name)])
    btn.append([InlineKeyboardButton(text="Отклонить", callback_data="Shift_Отклонить_%s" %name)])
    btn.append([InlineKeyboardButton(text="Отложить", callback_data="Shift_ Отложить_%s"%name)])
    worker_btn = InlineKeyboardMarkup(inline_keyboard=btn,)
    await bot.send_message(foremanid[0][2], "🕖 Рабочий %s только что попросил увеличить срок на %s дней по задаче '%s'.\n"
                                            "%s ➡️ %s"
                                            "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                            "Причина: %s"
                                            "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                            "Номер телефона рабочего: %s"
                                            "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                            "Пожалуйста завершите рабочий день, чтобы 'Одобрить' 'Отклонить' или 'Отложить' задачу."
                                            "\n➖➖➖➖➖➖➖➖➖➖➖\n" %(foremanid[0][0], data.get("dealine_time"), task_subj[0][0], task_subj[0][1], task_subj[0][2], mes ,foremanid[0][1]), reply_markup=worker_btn)
    task_name = data.get("task_name")
    cur.execute(
        "select subject, description, status, exp_start_date, exp_end_date, expected_time, comment_foreman from tabTask where name='%s'" % data.get("task_name"))
    task_subject = cur.fetchall()
    free_work = []
    if (task_subject[0][2] == "Working" or task_subject[0][2] == 'Report' or task_subject[0][2] == 'Cancelled'):
        free_work.append([InlineKeyboardButton(text="На исполнении ✅", callback_data="На исполнении ✅")])
        free_work.append([InlineKeyboardButton(text="Сделать отчет", callback_data="Отчет")])
        free_work.append([InlineKeyboardButton(text="Сдвинуть сроки", callback_data="Сдвинуть сроки")])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    else:
        free_work.append([InlineKeyboardButton(text="На исполнении", callback_data="На исполнении")])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(
        inline_keyboard=free_work,
    )
    if (task_subject[0][6]):
        await message.answer(text="Задача: %s "
                                       "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                       "Подробности задачи: %s "
                                       "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                       "Дата начала: %s\n"
                                       "Дата окончания: %s"
                                       "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                       "Ожидаемое время выполнения: %s часа(-ов)"
                                       "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                       "Комментарий по отчету: %s"
                                       "\n➖➖➖➖➖➖➖➖➖➖➖\n" % (
                                           task_subject[0][0], task_subject[0][1], task_subject[0][3],
                                           task_subject[0][4], task_subject[0][5], task_subject[0][6]),
                                  reply_markup=foreman_btn)
    else:
        await message.answer(text="Задача: %s "
                                       "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                       "Подробности задачи: %s "
                                       "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                       "Дата начала: %s\n"
                                       "Дата окончания: %s"
                                       "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                       "Ожидаемое время выполнения: %s часа(-ов)"
                                       "\n➖➖➖➖➖➖➖➖➖➖➖\n" % (
                                           task_subject[0][0], task_subject[0][1], task_subject[0][3],
                                           task_subject[0][4], task_subject[0][5]), reply_markup=foreman_btn)
    await state.update_data(task_name=task_name)
    await worker.task_profile.set()
@dp.message_handler(state=worker.input_task)
async def input_task(message: Message, state=FSMContext):
    conn.commit()
    tgid = message.from_user.id
    cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        conn.commit()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = await state.get_data()
        print(message)
        mes = message.text
        st = str(datetime.datetime.now()) + " " + str(data.get("task_name") + " " + str(tgid))
        cur.execute("select fio, phone_number, telegramid, foreman, dateobj, telegramidforeman from tabEmployer where telegramid=%s" % tgid)
        a = cur.fetchall()
        cur.execute("select phone_number from tabEmployer where telegramid=%s" % a[0][5])
        phone_foreman = cur.fetchall()
        mas = [data.get("task_name"), st, datetime.datetime.now(), "Administrator",
               data.get("task_subject"), data.get("parent_task_subject"), "", mes,
               a[0][0], tgid, a[0][1], a[0][3], a[0][5], phone_foreman[0][0], now]
        await state.update_data(date=now)
        cur.execute("insert into `tabTemp worker report` (task_name, name ,creation ,owner, "
                    "job, job_section, photo, job_value, worker_name, telegramid, phone_number, foreman_name, telegramidforeman, phone_number_foreman, date)"
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", mas)
        conn.commit()
        cur.execute("select history from tabTask where name=?", [data.get("task_name")])
        history_mas = cur.fetchall()
        if(history_mas and history_mas[0][0] != None):
            print(history_mas)
            history = '[' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' ' + a[0][0] + '] ' + mes + '\n' + history_mas[0][0]
        else:
            history = '[' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' ' + a[0][0] + '] ' + mes
        cur.execute("update tabTask set status='Report', amount=?, date=?, history=? where name=?", [mes, now, history ,data.get("task_name")])
        conn.commit()
        foreman_btn = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Нет")]],resize_keyboard=True)
        await message.answer("Отправьте фотографию выполненной работы, нажмите кнопку ""Нет"", если не требуется.", reply_markup=foreman_btn)
        await worker.reg_report.set()

@dp.message_handler(text="Нет", state=worker.reg_report)
async def photo(message: Message, state=FSMContext):
    conn.commit()
    await message.answer("Готово! Отчет отправлен!", reply_markup=ReplyKeyboardRemove())
    cur.execute("select name, subject, status from tabTask where workerID=? and progress < 100", [message.from_user.id])
    section_task = cur.fetchall()
    free_work = []
    for i in section_task:
        if (i[2] == 'Report'):
            free_work.append([InlineKeyboardButton(text="⚠ " + i[1], callback_data=i[0])])
        elif (i[2] == 'Cancelled'):
            free_work.append([InlineKeyboardButton(text="❌ " + i[1], callback_data=i[0])])
        else:
            free_work.append([InlineKeyboardButton(text=i[1], callback_data=i[0])])
    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(
        inline_keyboard=free_work,
    )
    await message.answer(text="Заявки", reply_markup=foreman_btn)
    await worker.section_task.set()

@dp.message_handler(state=worker.reg_report, content_types=['photo'])
async def photo_yes(message: Message, state=FSMContext):
    report = message.photo[-1]
    data = await state.get_data()
    print(data.get("count"))
    if(data.get("count")):
        count = int(data.get("count"))
    else:
        count = 1
    k = 0
    for i in range(5, 0, -1):
        if(os.path.exists("/home/erpnext/frappe-bench/sites/site1.local/public/files/" + data.get("task_name") + "_" + str(message.from_user.id) + "_" + str(i) +".jpg")):
            if(i != 5):
                cur.execute(f"update tabTask set photo{str(i + 1)}=? where name=?", ["/files/" + data.get("task_name") + "_" + str(message.from_user.id) + "_" + str(i + 1) + ".jpg", data.get("task_name")])
                conn.commit()
            os.rename("/home/erpnext/frappe-bench/sites/site1.local/public/files/" + data.get("task_name") + "_" + str(message.from_user.id) + "_" + str(i) +".jpg", "/home/erpnext/frappe-bench/sites/site1.local/public/files/" + data.get("task_name") + "_" + str(message.from_user.id) + "_" + str(i + 1) +".jpg")
    for i in range(1, 6):
        if(not os.path.exists("/home/erpnext/frappe-bench/sites/site1.local/public/files/" + data.get("task_name") + "_" + str(message.from_user.id) + "_" + str(i) +".jpg")):
            await report.download(destination="/home/erpnext/frappe-bench/sites/site1.local/public/files/" + data.get("task_name") + "_" + str(message.from_user.id) + "_" + str(i) + ".jpg")
            cur.execute(f"update `tabTemp worker report` set photo{str(i)}=? where task_name=? and telegramid=? and date=?",
                        ["/files/" + data.get("task_name") + "_" + str(message.from_user.id) + "_" + str(i) + ".jpg",
                         data.get("task_name"), message.from_user.id, data.get("date")])
            cur.execute(f"update tabTask set photo{str(i)}=? where name=?", ["/files/" + data.get("task_name") + "_" + str(message.from_user.id) + "_" + str(i) + ".jpg", data.get("task_name")])
            conn.commit()
            break
    free_work = []
    free_work.append([InlineKeyboardButton(text="Готово", callback_data="Готово")])
    foreman_btn = InlineKeyboardMarkup(
        inline_keyboard=free_work,
    )
    task_name = data.get("task_name")
    await state.update_data(task_name=task_name)
    if(count == 5):
        await message.answer("Готово! Отчет отправлен!")
        conn.commit()
        cur.execute("select name, subject, status from tabTask where workerID=? and progress < 100", [message.from_user.id])
        section_task = cur.fetchall()
        free_work = []
        for i in section_task:
            if (i[2] == 'Report'):
                free_work.append([InlineKeyboardButton(text="⚠" + i[1], callback_data=i[0])])
            elif (i[2] == 'Cancelled'):
                free_work.append([InlineKeyboardButton(text="❌" + i[1], callback_data=i[0])])
            else:
                free_work.append([InlineKeyboardButton(text=i[1], callback_data=i[0])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await message.answer(text="Заявки", reply_markup=foreman_btn)
        await state.update_data(count=1)
        await worker.section_task.set()
    else:
        await message.reply("Фотография скачана", reply_markup=ReplyKeyboardRemove())
        await message.answer("Вы можете отправить ещё %s фотографий \nНажмите готово, чтобы закончить отчёт" %(5 - count), reply_markup=foreman_btn)
        count += 1
        await state.update_data(count=count)
        await worker.reg_report.set()

@dp.callback_query_handler(state=worker.reg_report)
async def photo_cancel(call: CallbackQuery, state=FSMContext):
    call_data = call.data
    if(call_data == "Готово"):
        await bot.answer_callback_query(call.id, text="Готово! Отчет отправлен!", show_alert=True)
        conn.commit()
        cur.execute("select name, subject, status from tabTask where workerID=? and progress < 100",
                    [call.from_user.id])
        section_task = cur.fetchall()
        free_work = []
        for i in section_task:
            if (i[2] == 'Report'):
                free_work.append([InlineKeyboardButton(text="⚠" + i[1], callback_data=i[0])])
            elif (i[2] == 'Cancelled'):
                free_work.append([InlineKeyboardButton(text="❌" + i[1], callback_data=i[0])])
            else:
                free_work.append([InlineKeyboardButton(text=i[1], callback_data=i[0])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.answer(text="Заявки", reply_markup=foreman_btn)
        await state.update_data(count=1)
        await worker.section_task.set()

@dp.callback_query_handler(text_contains="serv:Закончить рабочий день", state=worker.job)
async def end_session(call: CallbackQuery, state=FSMContext):
    conn.commit()
    tgid = call.from_user.id
    cur.execute("select fio, telegramidforeman, foreman, object, phone_number from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await call.message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        mas = []
        now = datetime.datetime.now().strftime('%H:%M:%S')
        mas.append(now)
        mas.append(datetime.datetime.now().strftime('%Y-%m-%d'))
        mas.append(call.from_user.id)
        mes = []
        mes.append(datetime.datetime.now().strftime('%Y-%m-%d'))
        mes.append(tgid)
        cur.execute("select name, time_join from `tabWorker activity` where date=? and telegramid=?", mes)
        a = cur.fetchall()
        if(a):
            date = datetime.datetime.strptime(now, "%H:%M:%S") - datetime.datetime.strptime(a[0][1], "%H:%M:%S")
            cur.execute("select amountjob from tabWorker where telegramid=?", [call.from_user.id])
            amntjb = cur.fetchall()
            cur.execute("update `tabWorker activity` set time_end=? where date=? and telegramid=?", mas)
            cur.execute("update `tabWorker` set amountjob=? where telegramid=?", [float(amntjb[0][0]) + date.total_seconds() / 3600, call.from_user.id])
            conn.commit()
            await call.message.delete()
            free_work = []
            free_work.append([InlineKeyboardButton(text="Да", callback_data="Да")])
            free_work.append([InlineKeyboardButton(text="Выходной", callback_data="Выходной")])
            free_work.append([InlineKeyboardButton(text="Нет(иное)", callback_data="Нет(иное)")])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(
                inline_keyboard=free_work,
            )
            await call.message.answer(text="Планируете ли вы завтра выйти на работу? ", reply_markup=foreman_btn)
            await worker.reg_declaration.set()
        else:
            cur.execute("delete from `tabWorker activity temp` where telegramid=%s" %tgid)
            conn.commit()
            await call.message.delete()
            free_work = []
            free_work.append([InlineKeyboardButton(text="Да", callback_data="Да")])
            free_work.append([InlineKeyboardButton(text="Выходной", callback_data="Выходной")])
            free_work.append([InlineKeyboardButton(text="Нет(иное)", callback_data="Нет(иное)")])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
            )
            await call.message.answer(text="Планируете ли вы завтра выйти на работу? ", reply_markup=foreman_btn)
            await worker.reg_declaration.set()

@dp.callback_query_handler(state=worker.reg_declaration)
async def decl(call: CallbackQuery, state=FSMContext):
    call_data = call.data
    if(call_data == "Да"):
        await call.message.delete()
        await call.message.answer("Ваш рабочий день закончен", reply_markup=worker_start_job)
        cur.execute("update tabEmployer set activity=0 where name=?", [call.from_user.id])
        conn.commit()
        await state.finish()
    elif(call_data == "Выходной"):
        await call.message.delete()
        await call.message.answer("Ваш рабочий день закончен", reply_markup=worker_start_job)
        cur.execute("update tabEmployer set activity=0 where name=?", [call.from_user.id])
        conn.commit()
        await state.finish()
    elif(call_data == "Нет(иное)"):
        await call.message.edit_text("Почему? Укажите причину.")
        cur.execute("update tabEmployer set activity=0 where name=?", [call.from_user.id])
        conn.commit()
        await worker.input_declaration.set()
    elif(call_data == "Назад"):
        await call.message.edit_text("Главное меню", reply_markup=worker_menu)
        await worker.job.set()

@dp.message_handler(state=worker.input_declaration)
async def decl(message: Message, state=FSMContext):
    mes = message.text
    tgid = message.from_user.id
    cur.execute("select fio from tabEmployer where telegramid=?", [tgid])
    fio = cur.fetchall()
    date = datetime.datetime.now() + datetime.timedelta(days= 1)
    times = datetime.datetime.strftime(date, "%Y-%m-%d")
    now = datetime.datetime.now()
    cur.execute("insert into tabDeclaration (name ,creation ,owner ,fio ,telegramid, date, declaration) values (%s, %s, %s, %s, %s, %s, %s)",
                [str(now) + " " + str(tgid), datetime.datetime.now(), "Administrator", fio[0][0], tgid, times, mes])
    conn.commit()
    await message.answer("Ваше заявление направлено руководству.", reply_markup=worker_start_job)
    await state.finish()
