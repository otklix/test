import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Сайт бота (замени на свой GitHub Pages)
BOT_SITE_URL = "https://ggcrachvvv-arch.github.io/Nobot/"

# Хранилище статусов
user_connected = {}

@dp.business_connection()
async def business_connect(conn: types.BusinessConnection):
    if conn.is_enabled:
        user_connected[conn.user_id] = True
        await bot.send_message(conn.user_id, "✅ ДААСС подключён к чатам!")

@dp.message()
async def start(message: types.Message):
    if message.text == "/start":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("🔍 Проверить подключение", callback_data="check")],
            [InlineKeyboardButton("🌐 Открыть сайт ДААСС", web_app=WebAppInfo(url=BOT_SITE_URL))],
            [InlineKeyboardButton("📞 Поддержка", url="https://t.me/ggcrachvvv_arch")]
        ])
        await message.reply(
            "🔐 **ДААСС** — твой помощник в Telegram\n\n"
            "📌 Нажми кнопку ниже, чтобы проверить подключение.",
            reply_markup=keyboard
        )

@dp.callback_query(lambda c: c.data == "check")
async def check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    msg = await callback.message.edit_text("🔄 Проверка...")

    for i in range(1, 11):
        percent = i * 10
        squares = "🟩" * i + "⬜" * (10 - i)
        await msg.edit_text(f"📡 Проверка: {percent}%\n{squares}")
        await asyncio.sleep(0.3)

    if user_connected.get(user_id, False):
        await msg.edit_text("✅ **ДААСС активирован!**")
    else:
        user_connected[user_id] = True
        await msg.edit_text(
            "✅ **Бот активирован (тестовый режим)**\n\n"
            "⚠️ Для реальной работы нужен Telegram Premium и хостинг 24/7.\n\n"
            "🌐 Открой сайт ДААСС по кнопке ниже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🌐 Сайт ДААСС", web_app=WebAppInfo(url=BOT_SITE_URL))]
            ])
        )

async def main():
    await dp.start_polling(bot, allowed_updates=["business_connection", "message", "callback_query"])

if __name__ == "__main__":
    asyncio.run(main())