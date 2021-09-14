from aiogram import executor
from loader import dp
import asyncio
import middlewares, filters, handlers
from utils.notify_admins import on_startup_notify
import mariadb
from data.config import user, password, host, port, database
import sqlite3
from loader import bot
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, MediaGroup
btn = []
btn.append([InlineKeyboardButton(text="Понятно", callback_data="Понятно")])
bnt_inl = InlineKeyboardMarkup(
    inline_keyboard=btn,
)
async def notify():
    while True:
        connSql3 = sqlite3.connect("buffer.db")
        curSql3 = connSql3.cursor()
        curSql3.execute("create table if not exists Employer (name text, status text,telegramidforeman text)")
        conn = mariadb.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database
        )
        cur = conn.cursor()
#        print("Ищу обновления))")
        cur.execute("select name, status, telegramidforeman, foreman from tabEmployer")
        for name, status, tlForeman, foreman in cur:
#            print(f"Main DB - Name: {name}, Status: {status}, TeleID: {tlForeman}")
            curSql3.execute("select * from Employer where name=?", [name])
            a = curSql3.fetchall()
            if(a):
                for nameBuf, statusBuf, tlForemanBuf in a:
#                    print(f"Bufer DB - Name: {nameBuf}, Status: {statusBuf}, TeleID: {tlForemanBuf}")
                    if(nameBuf == name):
                        if(status != statusBuf):
                            if(status == 'Уволен'):
                                curSql3.execute("delete from Employer where name=?", [name])
                                connSql3.commit()
                                await bot.send_message(name,text=f"Вы уволены", reply_markup=ReplyKeyboardRemove())
                            elif(status == 'Подтвержден'):
                                curSql3.execute("update Employer set status=? where name=?", [status, name])
                                connSql3.commit()
                                await bot.send_message(name, text=f"Ваша учетная запись подтверждена, можете приступать к работе!", reply_markup=bnt_inl)
                            else:
                                curSql3.execute("update Employer set status=? where name=?", [status, name])
                                connSql3.commit()
                                await bot.send_message(name, text=f"Статус вашей учетной записи изменён с {statusBuf} на {status}", reply_markup=bnt_inl)
                        if(tlForemanBuf != tlForeman):
                            curSql3.execute("update Employer set telegramidforeman=? where name=?", [tlForeman, name])
                            connSql3.commit()
                            await bot.send_message(name, text=f"Вам назначен новый инженер - {foreman}", reply_markup=bnt_inl)
            else:
#                print(f"Завожу чувака с данными - Name: {name}, Status: {status}, TeleID: {tlForeman}")
                curSql3.execute("insert into Employer (name, status, telegramidforeman) values (?, ?, ?)", [name, status, tlForeman])
                connSql3.commit()
        conn.close()
        await asyncio.sleep(10)


async def on_startup(dispatcher):
    await on_startup_notify(dispatcher)
    asyncio.create_task(notify())
if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
