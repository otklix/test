import os
import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН")
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))
BASE_URL = "https://твой-логин.github.io/kaktus-rbiks/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === ХРАНИЛИЩЕ ===
orders = {}

# === КЛАВИАТУРА ===
def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🌵 Кактус РБикс", url=BASE_URL),
        InlineKeyboardButton("📦 Купить Robux", callback_data="buy"),
        InlineKeyboardButton("🆘 Помощь", callback_data="help")
    )
    return kb

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "🌵 Добро пожаловать в **Кактус РБикс**!\n\n"
        "💰 Здесь ты можешь купить Robux по низкой цене.\n"
        "📦 Выбери нужный пакет или перейди на сайт.",
        reply_markup=main_menu()
    )

@dp.callback_query(lambda c: c.data == "buy")
async def buy_callback(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("160 Robux", callback_data="robux_160"),
        InlineKeyboardButton("260 Robux", callback_data="robux_260"),
        InlineKeyboardButton("500 Robux", callback_data="robux_500"),
        InlineKeyboardButton("1000 Robux", callback_data="robux_1000"),
        InlineKeyboardButton("2500 Robux", callback_data="robux_2500"),
        InlineKeyboardButton("5000 Robux", callback_data="robux_5000")
    )
    await callback.message.edit_text("📦 Выбери пакет:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("robux_"))
async def process_robux(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[1])
    order_id = f"#{random.randint(100000, 999999)}"
    link = f"{BASE_URL}?robux={amount}"
    await callback.message.edit_text(
        f"✅ Ордер {order_id} создан!\n"
        f"Robux: {amount}\n"
        f"🔗 Перейди по ссылке для оплаты:\n{link}",
        disable_web_page_preview=True
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "help")
async def help_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🆘 **Помощь:**\n"
        "1. Выбери пакет.\n"
        "2. Перейди по ссылке.\n"
        "3. Оплати и получи Robux.\n\n"
        "❓ Вопросы — пиши @твой_ник"
    )
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())