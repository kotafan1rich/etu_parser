import asyncio
from src.checker.utils import sender
from src.create_bot import bot, dp
from src.checker.router import checker_router


async def on_startapp():
    await bot.delete_webhook()

    dp.include_router(checker_router)

    asyncio.create_task(sender())


async def polling():
    await dp.emit_startup(await on_startapp())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(polling())
