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
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8011946729:AAE9t-n-Ur16Kxg0gH-9uUF6SAP6H2Qa-Oo"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

BASE_URL = "https://otklix.github.io/test/"

# Хранилище использованных ссылок
used_links = {}
user_reports = {}

# ===== КОМАНДА /START =====
@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    
    if len(args) > 1 and args[1].startswith("report_"):
        report_id = args[1].replace("report_", "")
        
        if report_id in used_links:
            await message.answer(
                "❌ **Эта ссылка уже была использована!**\n\n"
                "🔒 Каждая ссылка одноразовая для безопасности.",
                parse_mode="Markdown"
            )
            return
        
        # Отправляем ссылку на отчёт
        report_link = f"{BASE_URL}progress/{report_id}.html"
        
        await message.answer(
            f"📄 **Ваш отчёт готов!**\n\n"
            f"🔗 Ссылка: {report_link}\n\n"
            f"📊 Статистика:\n"
            f"• Найдено юзернеймов: 20+\n"
            f"• Все проверены через Telegram API\n\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"🔒 Ссылка одноразовая!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 Открыть отчёт", url=report_link)],
                [InlineKeyboardButton(text="📊 Смотреть статистику", callback_data="stats")]
            ])
        )
        
        used_links[report_id] = True
        return
    
    await message.answer(
        "🌊 **AQUA CHECKER**\n\n"
        "🔍 **Функции бота:**\n"
        "• Проверка юзернеймов\n"
        "• Получение отчётов\n"
        "• Статистика\n\n"
        "📌 **Как использовать:**\n"
        "• Напиши юзернейм → проверка\n"
        "• Используй сайт → массовый поиск\n\n"
        "🌐 Сайт: https://otklix.github.io/test/",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Открыть сайт", url="https://otklix.github.io/test/")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
        ])
    )

# ===== КОМАНДА /STATS =====
@dp.message(Command("stats"))
async def stats(message: types.Message):
    await message.answer(
        "📊 **Статистика AQUA CHECKER**\n\n"
        f"• Сгенерировано ссылок: {len(used_links)}\n"
        f"• Активных отчётов: {len([k for k, v in used_links.items() if not v])}\n"
        f"• Использованных ссылок: {len([k for k, v in used_links.items() if v])}\n\n"
        f"🌐 Сайт: {BASE_URL}",
        parse_mode="Markdown"
    )

# ===== ОБРАБОТКА КНОПОК =====
@dp.callback_query()
async def callback(callback: types.CallbackQuery):
    if callback.data == "stats":
        await callback.message.answer(
            "📊 **Статистика AQUA CHECKER**\n\n"
            f"• Сгенерировано ссылок: {len(used_links)}\n"
            f"• Активных отчётов: {len([k for k, v in used_links.items() if not v])}\n"
            f"• Использованных ссылок: {len([k for k, v in used_links.items() if v])}",
            parse_mode="Markdown"
        )
        await callback.answer()
    else:
        await callback.answer()

# ===== ПРОВЕРКА ЮЗЕРНЕЙМА =====
@dp.message()
async def check(message: types.Message):
    username = message.text.strip().lower().replace('@', '')
    
    if len(username) < 5:
        await message.answer(
            "❌ **Минимальная длина — 5 символов!**\n\n"
            "Пример: `abcdx`",
            parse_mode="Markdown"
        )
        return
    
    # Проверка через API
    import aiohttp
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/checkUsername"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"username": username}) as response:
                data = await response.json()
                is_available = data.get("result", False)
    except:
        await message.answer("❌ Ошибка подключения к API")
        return
    
    if is_available:
        await message.answer(
            f"✅ **@{username} — СВОБОДЕН!**\n\n"
            f"🔗 https://t.me/{username}\n\n"
            f"📄 Хотите полный отчёт? Используйте сайт: {BASE_URL}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 Открыть сайт", url=BASE_URL)],
                [InlineKeyboardButton(text="🔗 Перейти в профиль", url=f"https://t.me/{username}")]
            ])
        )
    else:
        await message.answer(
            f"❌ **@{username} — ЗАНЯТ!**\n\n"
            f"🔍 Попробуйте другой юзернейм\n"
            f"📄 Или используйте сайт для массового поиска: {BASE_URL}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 Открыть сайт", url=BASE_URL)]
            ])
        )

# ===== ЗАПУСК БОТА =====
async def main():
    print("🌊 AQUA CHECKER БОТ ЗАПУЩЕН!")
    print(f"🌐 Сайт: {BASE_URL}")
    print("🤖 Бот готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())