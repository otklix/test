import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Хранилище статусов
user_connected = {}

@dp.business_connection()
async def business_connect(connection: types.BusinessConnection):
    if connection.is_enabled:
        user_connected[connection.user_id] = True
        await bot.send_message(connection.user_id, "✅ ДААСС подключён к чатам!")

@dp.message()
async def start(message: types.Message):
    if message.text == "/start":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить", callback_data="check")]
            ]
        )
        await message.reply("🔐 **ДААСС**\nНажми кнопку.", reply_markup=keyboard)

@dp.callback_query()
async def check(callback: types.CallbackQuery):
    if callback.data == "check":
        user_id = callback.from_user.id
        msg = await callback.message.edit_text("🔄 Проверка...")

        for i in range(1, 11):
            percent = i * 10
            squares = "🟩" * i + "⬜" * (10 - i)
            await msg.edit_text(f"📡 {percent}%\n{squares}")
            await asyncio.sleep(0.3)

        if user_connected.get(user_id, False):
            await msg.edit_text("✅ ДААСС активирован!")
        else:
            user_connected[user_id] = True
            await msg.edit_text("✅ Активирован (тест)")

async def main():
    await dp.start_polling(bot, allowed_updates=["business_connection", "message", "callback_query"])

if __name__ == "__main__":
    asyncio.run(main())