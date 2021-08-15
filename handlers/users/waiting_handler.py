from aiogram import dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from loader import dp
from states.wait_state import wait, wait_foremane
from database.connect_db import cur, conn
from states.worker import worker
from keyboards.default.worker_job import worker_start_job

@dp.message_handler(text="Проверить наличие обновлений", state=worker.no_job)
async def no_job(message: Message, state=FSMContext):
    conn.commit()
    cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" %message.from_user.id)
    a = cur.fetchall()
    if(a[0][0] == None or a[0][0] == '' or a[0][0] == " "):
        await message.answer("Добрый день, у вас нет руководителя, нажмите на кнопку, чтобы проверить обновления.")
        await worker.no_job.set()
    else:
        cur.execute("select fio from tabEmployer where name=?", [a[0][0]])
        fio = cur.fetchall()
        print(a[0][0], fio)
        name = fio[0][0]
        await message.answer("Вы присоединились к %s" %name, reply_markup=worker_start_job)
        await message.answer('Нажмите "Начать рабочий день", чтобы выйти на смену')
        await state.finish()
