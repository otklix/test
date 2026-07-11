import os
import asyncio
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== ТОКЕН ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (НЕ В КОДЕ!) =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Проверьте секреты GitHub или переменные Render.")

BASE_URL = "https://otklix.github.io/test/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище использованных ссылок
used_links = {}

# ===== КОМАНДА /START =====
@dp.message(Command("start"))
async def start(message: types.Message):
    text = message.text or ""
    args = text.split()
    
    print(f"📩 Получена команда: {text}")
    
    if len(args) > 1 and args[1].startswith("report_"):
        report_id = args[1].replace("report_", "")
        print(f"📄 Обработка отчёта: {report_id}")
        
        if report_id in used_links and used_links[report_id]:
            await message.answer(
                "❌ **Эта ссылка уже была использована!**\n\n"
                "🔒 Каждая ссылка одноразовая.",
                parse_mode="Markdown"
            )
            return
        
        report_link = f"{BASE_URL}progress/{report_id}.html"
        used_links[report_id] = True
        
        await message.answer(
            f"📄 **Ваш отчёт готов!**\n\n"
            f"🔗 Ссылка: {report_link}\n\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"🔒 Ссылка одноразовая!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 Открыть отчёт", url=report_link)]
            ])
        )
        return
    
    await message.answer(
        "🌊 **AQUA CHECKER**\n\n"
        "🔍 **Функции:**\n"
        "• Проверка юзернеймов\n"
        "• Получение отчётов\n\n"
        "🌐 Сайт: https://otklix.github.io/test/",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Открыть сайт", url="https://otklix.github.io/test/")]
        ])
    )

# ===== ПРОВЕРКА ЮЗЕРНЕЙМА =====
@dp.message()
async def check(message: types.Message):
    username = message.text.strip().lower().replace('@', '')
    
    if len(username) < 5:
        await message.answer("❌ Минимум 5 символов!")
        return
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/checkUsername"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"username": username}) as response:
                data = await response.json()
                is_available = data.get("result", False)
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        await message.answer("❌ Ошибка подключения к Telegram API")
        return
    
    if is_available:
        await message.answer(
            f"✅ @{username} — **СВОБОДЕН!**\n"
            f"🔗 https://t.me/{username}",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"❌ @{username} — **ЗАНЯТ!**\n\n"
            f"🔍 Попробуйте другой юзернейм",
            parse_mode="Markdown"
        )

# ===== ЗАПУСК =====
async def main():
    print("🌊 AQUA CHECKER БОТ ЗАПУЩЕН!")
    print(f"🌐 Сайт: {BASE_URL}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())