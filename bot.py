import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Хранилище статусов
user_connected = {}

@dp.business_connection_handler()
async def business_connect(connection: types.BusinessConnection):
    if connection.is_enabled:
        user_connected[connection.user_id] = True
        await bot.send_message(connection.user_id, "✅ ДААСС подключён к чатам!")

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("🔍 Проверить подключение", callback_data="check")
    keyboard.add(btn1)

    await message.reply(
        "🔐 **ДААСС** — твой помощник\n\n"
        "Нажми кнопку, чтобы проверить подключение.",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == "check")
async def check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    msg = await callback.message.edit_text("🔄 Проверка подключения...")

    for i in range(1, 11):
        percent = i * 10
        squares = "🟩" * i + "⬜" * (10 - i)
        await msg.edit_text(f"📡 Проверка: {percent}%\n{squares}")
        await asyncio.sleep(0.3)

    if user_connected.get(user_id, False):
        await msg.edit_text("✅ **ДААСС активирован!**")
    else:
        user_connected[user_id] = True
        await msg.edit_text("✅ **Бот активирован (тестовый режим)**")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)