from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from src.create_bot import bot

active_users = {
    1324716819,
    5149774783
}


checker_router = Router(name="checker_router")


@checker_router.message(Command("start"))
async def start(message: Message):
    active_users.add(message.from_user.id)
    await bot.send_message(
        message.from_user.id,
        "Этот бот отправялет позицию в списке ЛЭТИ и Политеха\n\nhttps://abit.etu.ru/ru/postupayushhim/lists/page/list#/?id=01978f26-62c1-7a35-8181-19d0798f1454\n\nhttps://my.spbstu.ru/home/abit/list-applicants/bachelor_pre_competition_lists",
    )
