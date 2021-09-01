from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, \
    MediaGroup
from loader import dp
from aiogram.dispatcher import FSMContext
from keyboards.default.foreman_job import foreman_start_job
from database.connect_db import conn, cur, cur1
import datetime
from loader import bot
from states.foreman import foreman
from keyboards.inline.foreman_menu import foreman_menu
import os.path
from keyboards.inline import worker_menu
@dp.message_handler(text="Начать рабочий день", state=foreman.start_job)
async def join_session(message: Message):
    now = datetime.datetime.now().strftime("%A")
    await message.answer("Добрый день, сегодня %s число." %now.strftime("%d-%m-%Y"), reply_markup=foreman_menu)
    await foreman.job.set()

@dp.callback_query_handler(text_contains="serv:Перенос сроков", state=foreman.job)
async def shift_deadlines(call: CallbackQuery, state=FSMContext):
    conn.commit()
    cur.execute("select name, task from tabshift_deadlines where foreman=? and status=?", [call.from_user.id, "На рассмотрении"])
    task_name = cur.fetchall()
    btn = []
    for i in task_name:
        cur.execute("select subject from tabTask where name=?", [i[1]])
        task_subject = cur.fetchall()
        btn.append([InlineKeyboardButton(text=task_subject[0][0], callback_data=i[0])])
    btn.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(inline_keyboard=btn,)
    await call.message.edit_text(text="Перенос сроков", reply_markup=foreman_btn)
    await foreman.action_deadlines.set()

@dp.callback_query_handler(state=foreman.action_deadlines)
async def action_deadlines(call: CallbackQuery, state=FSMContext):
    conn.commit()
    str = call.data
    if(str == "Назад"):
        await call.message.edit_text(text="Главное меню", reply_markup=foreman_menu)
        await foreman.job.set()
    else:
        btn = []
        cur.execute("select worker, task, cause, days from tabshift_deadlines where name=?", [str])
        data = cur.fetchall()
        cur.execute("select subject, exp_start_date, exp_end_date from tabTask where name=?", [data[0][1]])
        task_subj = cur.fetchall()
        cur.execute("select fio, phone_number where name=?", [data[0][0]])
        inf_wrkr = cur.fetchall()
        btn.append([InlineKeyboardButton(text="Одобрить", callback_data="Shift_Одобрить_%s" % str)])
        btn.append([InlineKeyboardButton(text="Отклонить", callback_data="Shift_Отклонить_%s" % str)])
        btn.append([InlineKeyboardButton(text="Отложить", callback_data="Shift_Отложить_%s" % str)])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=btn, )
        await call.message.edit_text(text="🕖 Рабочий %s попросил увеличить срок на %s дней по задаче '%s'.\n"
                                            "%s ➡️%s"
                                            "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                            "Причина: %s"
                                            "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                            "Номер телефона рабочего: %s"
                                            "\n➖➖➖➖➖➖➖➖➖➖➖\n" %(inf_wrkr[0][0], data[0][3], task_subj[0][0], task_subj[0][1], task_subj[0][2], data[0][2], inf_wrkr[0][1]), reply_markup=foreman_btn)
        await foreman.conf_deadlines.set()


@dp.callback_query_handler(state=foreman.conf_deadlines)
async def shift_yes_not(call: CallbackQuery, state=FSMContext):
    call_data = call.data
    mas = call_data.split('_')
    stat = await state.get_state()
    await state.update_data(state=stat)
    if (mas[1] == "Одобрить"):
        cur.execute("select days, task, name, worker  from tabshift_deadlines where name=?", [mas[2]])
        day = cur.fetchall()
        cur.execute("select exp_end_date, subject from tabTask where name=?", [day[0][1]])
        exp_end = cur.fetchall()
        cur.execute("update tabTask set exp_end_date=? where name=?",
                    [exp_end[0][0] + datetime.timedelta(days=int(day[0][0])), day[0][1]])
        conn.commit()
        cur.execute("update tabshift_deadlines set status='Одобрено' where name=? and status='На рассмотрении'",
                    [day[0][2]])
        conn.commit()
        await bot.answer_callback_query(call.id, text="Срок изменен", show_alert=True)
        await bot.send_message(day[0][3],
                               text="🕑 Инженер одобрил вашу просьбу по задаче %s, срок изменен." % exp_end[0][1])
        conn.commit()
        cur.execute("select name, task from tabshift_deadlines where foreman=? and status=?",
                    [call.from_user.id, "На рассмотрении"])
        task_name = cur.fetchall
        btn = []
        for i in task_name:
            cur.execute("select subject from tabTask where name=?", [i[1]])
            task_subject = cur.fetchall()
            btn.append([InlineKeyboardButton(text=task_subject[0][0], callback_data=i[0])])
        btn.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=btn, )
        await call.message.edit_text(text="Перенос сроков", reply_markup=foreman_btn)
        await foreman.job.set()
    elif (mas[1] == 'Отклонить'):
        await call.message.edit_text("Укажите комментарий")
        await state.update_data(name_shift=mas[2])
        await foreman.shift.set()
    elif (mas[1] == 'Отложить'):
        cur.execute("update tabshift_deadlines set status=? where name=?", ["Отложено", mas[2]])
        conn.commit()
        await bot.answer_callback_query(call.id, text="Готово!", show_alert=True)
        conn.commit()
        cur.execute("select name, task from tabshift_deadlines where foreman=? and status=?",
                    [call.from_user.id, "На рассмотрении"])
        task_name = cur.fetchall
        btn = []
        for i in task_name:
            cur.execute("select subject from tabTask where name=?", [i[1]])
            task_subject = cur.fetchall()
            btn.append([InlineKeyboardButton(text=task_subject[0][0], callback_data=i[0])])
        btn.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=btn, )
        await call.message.edit_text(text="Перенос сроков", reply_markup=foreman_btn)
        await foreman.job.set()
    elif (mas[1] == 'Назад'):
        conn.commit()
        cur.execute("select name, task from tabshift_deadlines where foreman=? and status=?",
                    [call.from_user.id, "На рассмотрении"])
        task_name = cur.fetchall
        btn = []
        for i in task_name:
            cur.execute("select subject from tabTask where name=?", [i[1]])
            task_subject = cur.fetchall()
            btn.append([InlineKeyboardButton(text=task_subject[0][0], callback_data=i[0])])
        btn.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=btn, )
        await call.message.edit_text(text="Перенос сроков", reply_markup=foreman_btn)
        await foreman.job.set()
@dp.message_handler(state=foreman.shift)
async def cancel(message: Message, state=FSMContext):
    mes = message.text
    data = await state.get_data()
    print(data.get("task_name"))
    cur.execute("select subject from tabTask where name=?", [data.get("task_name")])
    subj = cur.fetchall()
    cur.execute("update tabshift_deadlines set status='Отклонено' where name=?", [data.get("name_shift")])
    conn.commit()
    await bot.send_message(data.get("teleid"), "Инженер отклонил вашу просьбу по задаче %s."
                                               "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                               "Комментарий: %s" % (subj[0][0], mes))

    await message.answer("Готово!")
    conn.commit()
    cur.execute("select name, task from tabshift_deadlines where foreman=? and status=?",
                [message.from_user.id, "На рассмотрении"])
    task_name = cur.fetchall
    btn = []
    for i in task_name:
        cur.execute("select subject from tabTask where name=?", [i[1]])
        task_subject = cur.fetchall()
        btn.append([InlineKeyboardButton(text=task_subject[0][0], callback_data=i[0])])
    btn.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(inline_keyboard=btn, )
    await message.answer(text="Перенос сроков", reply_markup=foreman_btn)
    await foreman.job.set()

@dp.callback_query_handler(text_contains="serv:Список свободных рабочих", state=foreman.job)
async def free_work(call: CallbackQuery, state=FSMContext):
    conn.commit()
    cur.execute("select fio, telegramid from tabEmployer where telegramidforeman='' and role='ROLE-0002' and status='Подтвержден'")
    a = cur.fetchall()
    free_work = []
    for i in a:
        free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work,)
    await call.message.edit_text(text="Список свободных рабочих", reply_markup=foreman_btn)
    await foreman.free_worker.set()

@dp.callback_query_handler(state=foreman.free_worker)
async def free_work(call: CallbackQuery, state=FSMContext):
    conn.commit()
    str = call.data
    if (str == "Назад"):
        await call.message.edit_text(text="Главное меню", reply_markup=foreman_menu)
        await foreman.job.set()
    else:
        cur.execute("select fio, phone_number, telegramid, comments_foreman, photo, photo_pass, amounttask, amounttask_month, amounttask_cancel, amounttask_now, amounttask_cancel_now"
                    " from tabEmployer where role='ROLE-0002' and status='Подтвержден' and telegramid=%s" % str)
        a = cur.fetchall()
        free_work = []
        free_work.append([InlineKeyboardButton("Взять в подчинение", callback_data="Взять в подчинение")])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_choise_free_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text("Профиль рабочего %s\n"
                                "Номер телефона: %s"
                                "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                "Сделано всего: %s\n"
                                "Сделано за последний месяц: %s\n"
                                "Из них просрочено: %s"
                                "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                "Текущие поставленные: %s\n"
                                "Текущие просроченные: %s"
                                "\n➖➖➖➖➖➖➖➖➖➖➖\n" %(a[0][0], a[0][1], a[0][6], a[0][7], a[0][8], a[0][9], a[0][10]),
                                     reply_markup=foreman_choise_free_btn)
        await state.update_data(fio=a[0][0], phone_number=a[0][1], telegramid=a[0][2], comment=a[0][3], photo=a[0][4], passport=a[0][5])
        await foreman.free_worker_profile.set()

@dp.callback_query_handler(state=foreman.free_worker_profile)
async def invite_team(call: CallbackQuery, state=FSMContext):
    conn.commit()
    str = call.data
    telegram = call.from_user.id
    if (str == "Назад"):
        cur.execute("select fio, telegramid from tabEmployer where telegramidforeman='' and role='ROLE-0002' and status='Подтвержден'")
        a = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Список свободных рабочих", reply_markup=foreman_btn)
        await foreman.free_worker.set()
    else:
        mas_foreman = []
        now = datetime.datetime.now()
        data = await state.get_data()
        cur.execute("select fio, telegramid, object from tabEmployer where telegramid=%s" %telegram)
        mas_foreman = cur.fetchall()
        cur.execute("update tabEmployer set foreman=?, telegramidforeman=?, object=? where name=?", [mas_foreman[0][0], mas_foreman[0][1], mas_foreman[0][2], data.get("telegramid")])
        conn.commit()
        await bot.answer_callback_query(call.id, "Рабочий %s был переведён к вам!" %data.get("fio"), show_alert=True)
        cur.execute("select fio, telegramid from tabEmployer where telegramidforeman='' and role='ROLE-0002' and status='Подтвержден'")
        a = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.answer(text="Список свободных рабочих", reply_markup=foreman_btn)
        await foreman.free_worker.set()

#@dp.callback_query_handler(text_contains="serv:Журнал учёта рабочих", state=foreman.job)
#async def check_time(call: CallbackQuery, state=FSMContext):
    #cur.execute("select fio, telegramid from `tabWorker activity temp` where telegramidforeman=%s" %call.from_user.id)
    #a = cur.fetchall()
    #free_work = []
    #for i in a:
    #    free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
    #free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    #foreman_btn = InlineKeyboardMarkup(
    #    inline_keyboard=free_work,
    #)
    #await call.message.edit_text(text="Список отметившихся", reply_markup=foreman_btn)
    #await foreman.activity_worker.set()
    #cur.execute("select fio, telegramid ,activity from tabEmployer where telegramidforeman=%s" % call.from_user.id)
    #a = cur.fetchall()
    #free_work = []
    #for i in a:
    #    if(i[2]==0):
    #        free_work.append([InlineKeyboardButton(text="‼ "+i[0], callback_data=i[1])])
    #    else:
    #        free_work.append([InlineKeyboardButton(text="✅ "+i[0], callback_data=i[1])])
    #free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    #foreman_btn = InlineKeyboardMarkup(
    #    inline_keyboard=free_work,
    #)
    #await call.message.edit_text(text="Список отметившихся", reply_markup=foreman_btn)
    #await foreman.activity_worker.set()


@dp.callback_query_handler(state=foreman.activity_worker)
async def free_work(call: CallbackQuery, state=FSMContext):
    conn.commit()
    str = call.data
    if (str == "Назад"):
        await call.message.edit_text(text="Главное меню", reply_markup=foreman_menu)
        await foreman.job.set()
    #else:
    #    cur.execute("select fio, time_join, telegramidforeman, name, date from `tabWorker activity temp` where telegramid=%s" % str)
    #   a = cur.fetchall()
    #    cur.execute("select phone_number from tabWorker where telegramid=%s" % str)
    #    tg = cur.fetchall()
    #    free_work = []
    #    time_work = a[0][1]
    #    free_work.append([InlineKeyboardButton(text="Принять", callback_data="Принять")])
    #    free_work.append([InlineKeyboardButton(text="Отклонить", callback_data="Отклонить")])
    #    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    #    foreman_choise_free_btn = InlineKeyboardMarkup(
    #        inline_keyboard=free_work,
    #    )
    #    await call.message.edit_text("Имя рабочего %s\nНомер телефона: %s\nВремя прихода на работу: %s\nДата отчета: %s"
    #                                 %(a[0][0], tg[0][0], time_work, a[0][4]),reply_markup=foreman_choise_free_btn)
    #    await state.update_data(telegramid=str, fio=a[0][0], time_join=a[0][1], telegramidforeman=a[0][2], nameTaskActivity=a[0][3], date=a[0][4])
    #    await foreman.activity_worker_profile.set()

#@dp.callback_query_handler(state=foreman.activity_worker_profile)
#async def invite_team(call: CallbackQuery, state=FSMContext):
#    conn.commit()
#    stri = call.data
#    telegram = call.from_user.id
#    if (stri == "Назад"):
#        cur.execute(
#            "select fio, telegramid from `tabWorker activity temp` where telegramidforeman=%s" % call.from_user.id)
#        a = cur.fetchall()
#        free_work = []
#        for i in a:
#            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
#        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
#        foreman_btn = InlineKeyboardMarkup(
#            inline_keyboard=free_work,
#        )
#        await call.message.edit_text(text="Список отметившихся", reply_markup=foreman_btn)
#        await foreman.activity_worker.set()
#    elif(stri == "Принять"):
#        mas_foreman = []
#        now = datetime.datetime.now()
#        data = await state.get_data()
#        mas = []
#        st = ""
#        mas.append(data.get("nameTaskActivity"))
#        mas.append(datetime.datetime.now())
#        mas.append("Administrator")
#        mas.append(data.get("fio"))
#        mas.append(data.get("time_join"))
#        mas.append(data.get("date"))
#        mas.append(None)
#        mas.append(data.get("telegramid"))
#        mas.append(data.get("telegramidforeman"))
#        cur.execute(
#            "insert into `tabWorker activity` (name ,creation ,owner, fio, time_join, date, time_end, telegramid, telegramidforeman)"
#            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", mas)
#        mas = []
#        mas.append(data.get("telegramid"))
#       mas.append(data.get("time_join"))
#        cur.execute("delete from `tabWorker activity temp` where telegramid=? and time_join=?", mas)
#        conn.commit()
#        cur.execute(
#            "select fio, telegramid from `tabWorker activity temp` where telegramidforeman=%s" % call.from_user.id)
#        a = cur.fetchall()
#        free_work = []
#        await call.message.delete()
#        await call.message.answer("Принято!")
#        for i in a:
#            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
#        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
#        foreman_btn = InlineKeyboardMarkup(
#            inline_keyboard=free_work,
#        )
#        await call.message.answer(text="Список отметившихся", reply_markup=foreman_btn)
#        await foreman.activity_worker.set()
#    elif(stri == "Отклонить"):
#        data = await state.get_data()
#        temp = []
#        j = data.get("telegramid")
#        j = int(j)
#        await bot.send_message(j, "Сообщение от прораба: "
#                                  "Ваш данные начала работы отклонены!")
#        mes = []
#        mes.append(data.get("time_join"))
#        mes.append(data.get("telegramid"))
#        cur.execute("delete from `tabWorker activity temp` where time_join=? and telegramid=?", mes)
#        conn.commit()
#        await call.message.delete()
#        await call.message.answer("Отклонено!")
#        cur.execute(
#            "select fio, telegramid from `tabWorker activity temp` where telegramidforeman=%s" % call.from_user.id)
#        a = cur.fetchall()
#        free_work = []
#        for i in a:
#            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
#        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
#        foreman_btn = InlineKeyboardMarkup(
#            inline_keyboard=free_work,
#        )
#        await call.message.answer(text="Список отметившихся", reply_markup=foreman_btn)
#        await foreman.activity_worker.set()

@dp.callback_query_handler(text_contains="serv:Список подчиненных", state=foreman.job)
async def work(call: CallbackQuery, state=FSMContext):
    conn.commit()
    cur.execute("select fio, telegramid, activity from tabEmployer where status='Подтвержден' and role='ROLE-0002' and telegramidforeman=%s" %call.from_user.id)
    a = cur.fetchall()
    free_work = []
    for i in a:
        if (i[2] == 0):
            free_work.append([InlineKeyboardButton(text="‼ " + i[0], callback_data=i[1])])
        else:
            free_work.append([InlineKeyboardButton(text="✅ " + i[0], callback_data=i[1])])
    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(
        inline_keyboard=free_work,
    )
    await call.message.edit_text(text="Список подчиненных", reply_markup=foreman_btn)
    await foreman.worker.set()

@dp.callback_query_handler(state=foreman.worker)
async def free_work(call: CallbackQuery, state=FSMContext):
    conn.commit()
    str = call.data
    if (str == "Назад"):
        await call.message.edit_text(text="Главное меню", reply_markup=foreman_menu)
        await foreman.job.set()
    else:
        cur.execute(
            "select fio, phone_number, telegramid, comments_foreman, photo, photo_pass, amounttask, amounttask_month, amounttask_cancel, amounttask_now, amounttask_cancel_now"
            " from tabEmployer where role='ROLE-0002' and status='Подтвержден' and telegramid=%s" % str)
        a = cur.fetchall()
        free_work = []
        free_work.append([InlineKeyboardButton(text="Удалить", callback_data="Удалить")])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_choise_free_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text("Профиль рабочего %s\n"
                                "Номер телефона: %s"
                                "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                "Сделано всего: %s\n"
                                "Сделано за последний месяц: %s\n"
                                "Из них просрочено: %s"
                                "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                "Текущие поставленные: %s\n"
                                "Текущие просроченные: %s"
                                "\n➖➖➖➖➖➖➖➖➖➖➖\n" %(a[0][0], a[0][1], a[0][6], a[0][7], a[0][8], a[0][9], a[0][10]),
                                     reply_markup=foreman_choise_free_btn)
        await state.update_data(fio=a[0][0], phone_number=a[0][1], telegramid=a[0][2], comment=a[0][3], photo=a[0][4], passport=a[0][5])
        await foreman.worker_profile.set()

@dp.callback_query_handler(state=foreman.worker_profile)
async def invite_team(call: CallbackQuery, state=FSMContext):
    conn.commit()
    str = call.data
    telegram = call.from_user.id
    if (str == "Назад"):
        conn.commit()
        cur.execute(
            "select fio, telegramid, activity from tabEmployer where status='Подтвержден' and role='ROLE-0002' and telegramidforeman=%s" % call.from_user.id)
        a = cur.fetchall()
        free_work = []
        for i in a:
            if (i[2] == 0):
                free_work.append([InlineKeyboardButton(text="‼ " + i[0], callback_data=i[1])])
            else:
                free_work.append([InlineKeyboardButton(text="✅ " + i[0], callback_data=i[1])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Список подчиненных", reply_markup=foreman_btn)
        await foreman.worker.set()
    elif(str == "Удалить"):
        now = datetime.datetime.now()
        data = await state.get_data()
        cur.execute("update tabEmployer set telegramidforeman='', foreman='', dateobj='', object='', activity=0  where telegramid=%s" %data.get("telegramid"))
        conn.commit()
        await bot.answer_callback_query(call.id, text="Рабочий %s был перенесён в архив!" %data.get("fio"), show_alert=True)
        conn.commit()
        cur.execute(
            "select fio, telegramid, activity from tabEmployer where status='Подтвержден' and role='ROLE-0002' and telegramidforeman=%s" % call.from_user.id)
        a = cur.fetchall()
        free_work = []
        for i in a:
            if (i[2] == 0):
                free_work.append([InlineKeyboardButton(text="‼ " + i[0], callback_data=i[1])])
            else:
                free_work.append([InlineKeyboardButton(text="✅ " + i[0], callback_data=i[1])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Список подчиненных", reply_markup=foreman_btn)
        await foreman.worker.set()

@dp.callback_query_handler(text_contains="serv:Просроченные задачи", state=foreman.job)
async def cancelled(call: CallbackQuery, state=FSMContext):
    conn.commit()
    cur.execute("select subject, name, workerid from tabTask where status='Overdue'")
    tasks = cur.fetchall()
    print(len(tasks))
    free_work = []
    if(len(tasks) > 10):
        j = 0
        free_work.append([InlineKeyboardButton(text="Следующая страница ➡", callback_data="Следующая страница")])
        for i in tasks[0:10]:
            j += 1
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
        await state.update_data(items=j, page=j/10)
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    else:
        for i in tasks:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work,)
    await call.message.edit_text(text="Просроченные задачи", reply_markup=foreman_btn)
    await foreman.overdue.set()

@dp.callback_query_handler(state=foreman.overdue)
async def choise_overdue(call: CallbackQuery, state=FSMContext):
    if(call.data == "Назад"):
        await call.message.edit_text("Главное меню", reply_markup=foreman_menu)
        await foreman.job.set()
    elif(call.data == "Следующая страница"):
        print("Следующая страница")
        cur.execute("select subject, name, workerid from tabTask where status='Overdue'")
        tasks = cur.fetchall()
        free_work = []
        data = await state.get_data()
        j = data.get('items')
        print(len(tasks[j:]))
        print(j)
        print(len(tasks[j:])//10)
        print(len(tasks[j:])//10 > 1)
        if(len(tasks[j:])/10 > 1):
            print(1)
            free_work.append([InlineKeyboardButton(text="Следующая страница ➡", callback_data="Следующая страница")])
            for i in tasks[j:j+10]:
                print('task: ',i)
                free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
            free_work.append([InlineKeyboardButton(text="Прерыдущая страница ⬅", callback_data="Предыдущая страница")])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            j += 10
            await state.update_data(items=(j))
            foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work,)
            pages = len(tasks)//10
            if(len(tasks)%10 != 0 ):
                pages = len(tasks)//10 + 1
            await call.message.edit_text("Просроченные задачи страница: %s из %s" %(j//10, pages), reply_markup=foreman_btn)
            await foreman.overdue.set()
        else:
            print(2)
            for i in tasks[j:]:
                free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
            free_work.append([InlineKeyboardButton(text="Прерыдущая страница ⬅", callback_data="Предыдущая страница")])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            j += 10
            foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work, )
            pages = len(tasks) // 10
            if (len(tasks) % 10 != 0):
                pages = len(tasks) // 10 + 1
            await call.message.edit_text("Просроченные задачи страница: %s из %s" %(j//10, pages), reply_markup=foreman_btn)
            await state.update_data(items=(j))
            await foreman.overdue.set()
    elif(call.data == "Предыдущая страница"):
        cur.execute("select subject, name, workerid from tabTask where status='Overdue'")
        tasks = cur.fetchall()
        print(len(tasks))
        free_work = []
        data = await state.get_data()
        j = data.get('items')
        print(j)
        print(len(tasks[:j]))
        j -= 10
        if(len(tasks[:j])/10 > 1):
            print(1)
            free_work.append([InlineKeyboardButton(text="Следующая страница ➡", callback_data="Следующая страница")])
            for i in tasks[(j - 10):j]:
                    free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
            free_work.append([InlineKeyboardButton(text="Прерыдущая страница ⬅", callback_data="Предыдущая страница")])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            await state.update_data(items=(j))
            foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work,)
            await call.message.edit_text("Просроченные задачи страница: %s из %s" % (j // 10, len(tasks)//10), reply_markup=foreman_btn)
            await foreman.overdue.set()
        else:
            print(2)
            free_work.append([InlineKeyboardButton(text="Следующая страница ➡", callback_data="Следующая страница")])
            for i in tasks[:j]:
                free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            await state.update_data(items=(j))
            foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work,)
            pages = len(tasks) // 10
            if (len(tasks) % 10 != 0):
                pages = len(tasks) // 10 + 1
            await call.message.edit_text("Просроченные задачи страница: %s из %s" %(j//10, pages), reply_markup=foreman_btn)
            await foreman.overdue.set()
    else:
        conn.commit()
        cur.execute("select workerid, subject, date_progress, date_perfomance from tabTask where name=?", [call.data])
        task = cur.fetchall()
        if(task):
            cur.execute("select fio from tabEmployer where name=?", [task[0][0]])
            fio = cur.fetchall()
            if(fio):
                free_work = []
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
                foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work, )
                await call.message.edit_text("Рабочий %s только что просрочил %s"
                                             "\n➖➖➖➖➖➖➖➖➖➖➖\n"
                                             "Рабочий просмотрел заявку: %s\n"
                                             "Рабочий начал исполнение: %s\n" %(fio[0][0], task[0][1], task[0][3], task[0][2]), reply_markup=foreman_btn)
                await foreman.overdue_down.set()
@dp.callback_query_handler(state=foreman.overdue_down)
async def back_overdue(call: CallbackQuery, state=FSMContext):
    if(call.data == "Назад"):
        conn.commit()
        cur.execute("select subject, name, workerid from tabTask where status='Overdue'")
        tasks = cur.fetchall()
        free_work = []
        if (len(tasks) > 10):
            j = 0
            free_work.append([InlineKeyboardButton(text="Следующая страница ➡", callback_data="Следующая страница")])
            for i in tasks[0:10]:
                j += 1
                free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
            await state.update_data(items=j, page=j / 10)
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        else:
            for i in tasks:
                free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work, )
        await call.message.edit_text(text="Просроченные задачи", reply_markup=foreman_btn)
        await foreman.overdue.set()

@dp.callback_query_handler(text_contains="serv:Список отчетов", state=foreman.job)
async def work(call: CallbackQuery, state=FSMContext):
    conn.commit()
    cur.execute("select distinct workerid from tabTask where status='Report'")
    worker_teleg = cur.fetchall()
    free_work = []
    for i in worker_teleg:
        cur.execute("select fio from tabEmployer where telegramid=? and telegramidforeman=?", [i[0], call.from_user.id])
        name = cur.fetchall()
        if(name):
            free_work.append([InlineKeyboardButton(text=name[0][0], callback_data=i[0])])
    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work,)
    await call.message.edit_text(text="Список отчетов", reply_markup=foreman_btn)
    await foreman.report_temp.set()

@dp.callback_query_handler(state=foreman.report_temp)
async def work(call: CallbackQuery, state=FSMContext):
    conn.commit()
    call_data = call.data
    if(call_data == "Назад"):
        await call.message.edit_text(text="Главное меню", reply_markup=foreman_menu)
        await foreman.job.set()
    else:
        cur.execute("select name, subject from tabTask where workerid=? and status='Report'", [call_data])
        a = cur.fetchall()
        cur.execute("select fio from tabEmployer where name=?", [call_data])
        b = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[1] , callback_data=i[0] + "+" + call_data)])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work,)
        await call.message.edit_text(text="Список отчетов рабочего %s" %b[0][0], reply_markup=foreman_btn)
        await foreman.report_temp_down.set()

@dp.callback_query_handler(state=foreman.report_temp_down)
async def free_work(call: CallbackQuery, state=FSMContext):
    conn.commit()
    call_data = call.data
    if (call_data == "Назад"):
        conn.commit()
        cur.execute("select distinct workerid from tabTask where status='Report'")
        worker_teleg = cur.fetchall()
        free_work = []
        for i in worker_teleg:
            cur.execute("select fio from tabEmployer where telegramid=? and telegramidforeman=?",
                        [i[0], call.from_user.id])
            name = cur.fetchall()
            if (name):
                free_work.append([InlineKeyboardButton(text=name[0][0], callback_data=i[0])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work, )
        await call.message.edit_text(text="Список отчетов", reply_markup=foreman_btn)
        await foreman.report_temp.set()
    else:
        mas = call_data.split("+")
        cur.execute("select name, subject, amount, date from tabTask where name=? and workerid=?", mas)
        a = cur.fetchall()
        cur.execute("select fio, phone_number, telegramidforeman from tabEmployer where name=?", [mas[1]])
        b = cur.fetchall()
        free_work = []
        free_work.append([InlineKeyboardButton(text="Принять", callback_data="Принять")])
        free_work.append([InlineKeyboardButton(text="Отклонить", callback_data="Отклонить")])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_choise_free_btn = InlineKeyboardMarkup(inline_keyboard=free_work,)
        await call.message.delete()
        media = MediaGroup()
        k = 1
        for i in range(1, 6):
            if(os.path.exists("/home/erpnext/frappe-bench/sites/site1.local/public/files/" + mas[0] + "_" + str(mas[1]) + "_" + str(i) + ".jpg")):
                media.attach_photo(open("/home/erpnext/frappe-bench/sites/site1.local/public/files/" + mas[0] + "_" + str(mas[1]) + "_" + str(i) + ".jpg" , 'rb'))
                k = 2
                #await bot.send_photo(call.from_user.id, photo=open("/home/erpnext/frappe-bench/sites/site1.local/public/files/" + mas[0] + str(mas[1]) + a[0][3] + "_" + str(i) + ".jpg" , 'rb'))
        if(k == 2):
            await bot.send_media_group(call.from_user.id, media=media)
        await call.message.answer("Название работы: %s\nТекст отчёта: %s\nНомер телефона рабочего: %s\nИмя рабочего: %s" %(a[0][1], a[0][2], b[0][1], b[0][0]), reply_markup=foreman_choise_free_btn)
        await state.update_data(telegramid_report=mas[1], date=a[0][3], task_name=a[0][0])
        await foreman.report_temp_profile.set()

@dp.callback_query_handler(state=foreman.report_temp_profile)
async def invite_team(call: CallbackQuery, state=FSMContext):
    conn.commit()
    call_data = call.data
    telegram = call.from_user.id
    if (call_data == "Назад"):
        data = await state.get_data()
        cur.execute("select name, subject from tabTask where workerid=? and status='Report'", [data.get("telegramid_report")])
        a = cur.fetchall()
        cur.execute("select fio from tabEmployer where name=?", [data.get("telegramid_report")])
        b = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[1], callback_data=i[0] + "+" + data.get("telegramid_report"))])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work, )
        await call.message.edit_text(text="Список отчетов рабочего %s" % b[0][0], reply_markup=foreman_btn)
        await foreman.report_temp_down.set()
    elif(call_data == "Принять"):
        a = []
        now = datetime.datetime.now()
        data = await state.get_data()
        await state.update_data(telegramid_report=data.get("telegramid_report"))
        progress = float(100)
        cur.execute("update tabTask set progress=?, status='Completed' where name=? and workerid=?", [float(progress), data.get("task_name"), data.get("telegramid_report")])
        conn.commit()
        await bot.answer_callback_query(call.id, text="Готово! Отчет занесён в базу!", show_alert=True)
        tempa = [data.get("telegramid_report"), call.from_user.id]
        cur.execute("select amounttask, amountjob, amounttask_now from tabEmployer where telegramid=?", [data.get("telegramid_report")])
        amount = cur.fetchall()
        amount_task = int(amount[0][0]) + 1
        rate = float(amount[0][1]) / float(amount_task)
        amounttask_now = int(amount[0][2]) - 1
        cur.execute("update tabEmployer set amounttask=?, rate=?, amounttask_now=? where name=?", [amount_task, rate,amounttask_now, data.get("telegramid_report")])
        conn.commit()
        cur.execute("select name, subject from tabTask where workerid=? and status='Report'", [tempa[0]])
        a = cur.fetchall()
        cur.execute("select fio from tabEmployer where name=?", [tempa[0]])
        b = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[1], callback_data=i[0] + "+" + tempa[0])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work, )
        await call.message.edit_text(text="Список отчетов рабочего %s" % b[0][0], reply_markup=foreman_btn)
        await foreman.report_temp_down.set()
    elif (call_data == "Отклонить"):
        data = await state.get_data()
        temp = [data.get("telegramid_report"), data.get("job"), data.get("date")]
        await state.update_data(telegramid_report=data.get("telegramid_report"))
        conn.commit()
        await call.message.delete()
        conn.commit()
        tempa = [data.get("telegramid_report"), call.from_user.id]
        free_work = []
        free_work.append([InlineKeyboardButton(text="Отклонить отчёт без комментария", callback_data="Подтвердить")])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work, )
        await call.message.answer("Пожалуйста, напишите причину отклонения отчёта. \nВы можете нажать `Отклонить отчёт без комментария`, чтобы не писать комментарий.\n",
            reply_markup=foreman_btn)
        await foreman.cancel_report.set()

@dp.callback_query_handler(state=foreman.cancel_report)
async def back_to_profile(call: CallbackQuery, state=FSMContext):
    call_back = call.data
    if(call_back == "Назад"):
        data = await state.get_data()
        cur.execute("select name, subject from tabTask where workerid=? and status='Report'",
                    [data.get("telegramid_report")])
        a = cur.fetchall()
        cur.execute("select fio from tabEmployer where name=?", [data.get("telegramid_report")])
        b = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append(
                [InlineKeyboardButton(text=i[1], callback_data=i[0] + "+" + [data.get("telegramid_report")])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work, )
        await call.message.edit_text(text="Список отчетов рабочего %s" % b[0][0], reply_markup=foreman_btn)
        await foreman.report_temp_down.set()
    elif(call_back == "Подтвердить"):
        data = await state.get_data()
        temp = [data.get("telegramid_report"), data.get("job"), data.get("date")]
        await state.update_data(telegramid_report=data.get("telegramid_report"))
        cur.execute("select fio from tabEmployer where name=?", [call.from_user.id])
        name = cur.fetchall()
        cur.execute("select history from tabTask where name=?", [data.get("task_name")])
        history_mas = cur.fetchall()
        if (history_mas and history_mas[0][0] != None):
            history = '[' + datetime.datetime.now().strftime("'%Y-%m-%d %H:%M:%S") + ']' + name[0][0] + '] ' + "Причина не указана" + '\n' + \
                      history_mas[0][0]
        else:
            history = '[' + datetime.datetime.now().strftime("'%Y-%m-%d %H:%M:%S") + ' ' + name[0][0] + '] ' + "Причина не указана"
        cur.execute("update tabTask set status='Cancelled', history=? where workerid=? and name=?", [history, data.get("telegramid_report"), data.get("task_name")])
        conn.commit()
        await bot.answer_callback_query(call.id, text="Готово! Отчет отклонён!", show_alert=True)
        cur.execute("select name, subject from tabTask where workerid=? and status='Report'",
                    [data.get("telegramid_report")])
        a = cur.fetchall()
        cur.execute("select fio from tabEmployer where name=?", [data.get("telegramid_report")])
        b = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append(
                [InlineKeyboardButton(text=i[1], callback_data=i[0] + "+" + data.get("telegramid_report"))])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work, )
        await call.message.edit_text(text="Список отчетов рабочего %s" % b[0][0], reply_markup=foreman_btn)
        await foreman.report_temp_down.set()

@dp.message_handler(state=foreman.cancel_report)
async def cancel_report(message: Message, state=FSMContext):
    data = await state.get_data()
    mes = message.text
    temp = [data.get("telegramid_report"), data.get("task_name"), data.get("date")]
    await state.update_data(telegramid_report=data.get("telegramid_report"))
    cur.execute("select comment_foreman from tabTask where workerid=? and name=?", temp)
    comment = cur.fetchall()
    if(comment[0][0]):
        comment_answer = comment[0][0] + "\n" + mes
    else:
        comment_answer = mes
    #await bot.send_message(data.get("telegramid_report"), "Ваш отчет по задаче '%s' отклонили!\nКомментарий: %s" %(temp[1], mes))
    cur.execute("select fio from tabEmployer where name=?", [message.from_user.id])
    name = cur.fetchall()
    cur.execute("select history from tabTask where name=?", [data.get("task_name")])
    history_mas = cur.fetchall()
    if (history_mas and history_mas[0][0] != None):
        history = '[' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' ' + name[0][
            0] + '] ' + mes + '\n' + \
                  history_mas[0][0]
    else:
        history = '[' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' ' + name[0][0] + '] ' + mes
    cur.execute("update tabTask set comment_foreman=?, status='Cancelled', amount='', history=? where workerid=? and name=?", [comment_answer, history, temp[0], temp[1]])
    conn.commit()
    await message.answer("Отчёт отклонен.")
    temp = []
    temp.append(data.get("telegramid_report"))
    conn.commit()
    tempa = [temp[0], message.from_user.id]
    cur.execute("select name, subject from tabTask where workerid=? and status='Report'",
                [data.get("telegramid_report")])
    a = cur.fetchall()
    cur.execute("select fio from tabEmployer where name=?", [data.get("telegramid_report")])
    b = cur.fetchall()
    free_work = []
    for i in a:
        free_work.append(
            [InlineKeyboardButton(text=i[1], callback_data=i[0] + "+" + data.get("telegramid_report"))])
    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work, )
    await message.answer(text="Список отчетов рабочего %s" % b[0][0], reply_markup=foreman_btn)
    await foreman.report_temp_down.set()

@dp.callback_query_handler(text_contains="serv:Закончить рабочий день", state=foreman.job)
async def end_session(call: CallbackQuery, state=FSMContext):
    now = datetime.datetime.now()
    await call.message.delete()
    await call.message.answer(text="Вы закончили рабочий день", reply_markup=foreman_start_job)
    await state.finish()