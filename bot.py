import os
import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Хранилище статусов подключения (временно, в памяти)
user_connected = {}

@dp.business_connection()
async def handle_business_connection(connection: types.BusinessConnection):
    if connection.is_enabled:
        user_connected[connection.user_id] = True
        logging.info(f"✅ ДААСС подключён к пользователю {connection.user_id}")
        await bot.send_message(connection.user_id, "✅ ДААСС успешно подключён к твоим чатам!")

@dp.message()
async def start(message: types.Message):
    if message.text == "/start":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("🔍 Проверить подключение", callback_data="check_connection")]
        ])
        await message.reply(
            "🔐 **ДААСС**\n\n"
            "📌 Чтобы активировать бота:\n"
            "1️⃣ Включи Secretary Mode в BotFather\n"
            "2️⃣ Подключи бота в Настройки → Автоматизация чатов\n"
            "3️⃣ Нажми кнопку ниже для проверки\n\n"
            "⏳ После проверки бот начнёт видеть чаты.",
            reply_markup=keyboard
        )

@dp.callback_query(lambda c: c.data == "check_connection")
async def check_connection(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    # Анимация проверки
    msg = await callback.message.edit_text(
        "🔄 **Проверка подключения...**\n\n"
        "⏳ 0 сек\n"
        "🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%"
    )

    # Имитация проверки с таймером (реальная проверка — через business_connection)
    for i in range(1, 11):
        percent = i * 10
        squares = "🟩" * i + "⬜" * (10 - i)
        await msg.edit_text(
            f"🔄 **Проверка подключения...**\n\n"
            f"⏳ {i} сек\n"
            f"{squares} {percent}%"
        )
        await asyncio.sleep(0.5)

    # Реальная проверка: был ли business_connection
    if user_connected.get(user_id, False):
        await msg.edit_text(
            "✅ **ДААСС подключён!**\n\n"
            "Теперь бот видит все твои чаты.\n"
            "Удалённые сообщения будут приходить сюда."
        )
    else:
        await msg.edit_text(
            "❌ **ДААСС не подключён!**\n\n"
            "📌 Проверь:\n"
            "1️⃣ Telegram Premium активен?\n"
            "2️⃣ Бот добавлен в Настройки → Автоматизация чатов?\n"
            "3️⃣ Ты написал кому-нибудь сообщение ПОСЛЕ добавления?\n\n"
            "🔄 Попробуй снова после выполнения условий.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🔄 Проверить снова", callback_data="check_connection")]
            ])
        )

async def main():
    await dp.start_polling(bot, allowed_updates=["business_connection", "message", "callback_query"])

if __name__ == "__main__":
    asyncio.run(main())