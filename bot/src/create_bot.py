import logging
from aiogram import Bot, Dispatcher
from src.config import settings

logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (INFO, DEBUG, WARNING, ERROR)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Формат сообщений
)

bot = Bot(token=settings.TOKEN)
dp = Dispatcher()
