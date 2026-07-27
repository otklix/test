import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.business_connection()
async def business_connect(conn: types.BusinessConnection):
    if conn.is_enabled:
        await bot.send_message(conn.user_id, "✅ Бот подключён к чатам!")

@dp.business_message()
async def business_msg(msg: types.Message):
    logging.info(f"Сообщение: {msg.text}")

@dp.message()
async def start(msg: types.Message):
    if msg.text == "/start":
        await msg.reply("🔐 Бот запущен. Подключи в Настройки → Автоматизация чатов")

async def main():
    await dp.start_polling(bot, allowed_updates=["business_connection", "business_message", "message"])

if __name__ == "__main__":
    asyncio.run(main())