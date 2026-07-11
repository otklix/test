import os
import json
import asyncio
import random
import string
import zipfile
import io
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8011946729:AAE9t-n-Ur16Kxg0gH-9uUF6SAP6H2Qa-Oo"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

REPORTS_DIR = "reports"
PROGRESS_DIR = "progress"
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(PROGRESS_DIR, exist_ok=True)

# ===== БАЗОВЫЙ URL (ваш сайт) =====
BASE_URL = "https://otklix.github.io/test/"

used_links = {}

# ===== ОТПРАВКА ССЫЛКИ В ОТВЕТ =====
@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    
    if len(args) > 1 and args[1].startswith("report_"):
        report_id = args[1].replace("report_", "")
        
        if report_id in used_links:
            await message.answer("❌ Эта ссылка уже была использована!")
            return
        
        # Формируем ссылку на отчёт
        report_link = f"{BASE_URL}progress/{report_id}.html"
        
        # Отправляем ответ со ссылкой
        await message.answer(
            f"📄 **Ваш отчёт готов!**\n\n"
            f"🔗 Ссылка: {report_link}\n\n"
            f"📊 Найдено юзернеймов: 20+\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"🔒 Ссылка одноразовая!",
            parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🌐 Открыть отчёт", url=report_link)],
                [types.InlineKeyboardButton(text="📲 Открыть в Telegram", url=f"https://t.me/{BOT_TOKEN.split(':')[0]}")]
            ])
        )
        
        used_links[report_id] = True
        return
    
    await message.answer(
        "🌊 **AQUA CHECKER**\n\n"
        "🔍 Напиши юзернейм для проверки\n"
        "📄 Используй сайт для массового поиска\n\n"
        "🌐 Сайт: https://otklix.github.io/test/",
        parse_mode="Markdown"
    )

@dp.message()
async def check(message: types.Message):
    username = message.text.strip().lower().replace('@', '')
    
    if len(username) < 5:
        await message.answer("❌ Минимум 5 символов!")
        return
    
    import aiohttp
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/checkUsername"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"username": username}) as response:
            data = await response.json()
            is_available = data.get("result", False)
    
    if is_available:
        await message.answer(
            f"✅ @{username} — **СВОБОДЕН!**\n"
            f"🔗 https://t.me/{username}\n\n"
            f"📄 Хотите полный отчёт? Используйте сайт: https://otklix.github.io/test/",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"❌ @{username} — **ЗАНЯТ!**\n\n"
            f"🔍 Попробуйте другой юзернейм или используйте сайт для массового поиска: https://otklix.github.io/test/",
            parse_mode="Markdown"
        )

async def main():
    print("🌊 AQUA CHECKER БОТ ЗАПУЩЕН!")
    print(f"🌐 Сайт: {BASE_URL}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())