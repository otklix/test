import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен берется из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logging.error("BOT_TOKEN не найден! Установите секрет в настройках GitHub.")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "👋 Привет! Я бот из репозитория otklix/wait.\n"
        "Я работаю через GitHub Actions!"
    )

@dp.message()
async def echo_message(message: types.Message):
    """Отвечает на любое сообщение"""
    await message.answer(f"Вы написали: {message.text}")

async def main():
    """Запуск бота"""
    logging.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())