import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import secrets

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))  # Твой ID, но не используется для ссылок

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Хранилище: {код: chat_id}
LINKS_FILE = 'links.json'

def load_links():
    try:
        with open(LINKS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_links(links):
    with open(LINKS_FILE, 'w') as f:
        json.dump(links, f)

@dp.message_handler(commands=['start'])
async def start_cmd(message: Message):
    await message.answer(
        "📍 Создай ссылку, чтобы узнать где находится человек\n\n"
        "Нажми кнопку ниже 👇",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔗 Создать ссылку", callback_data="create_link")
        )
    )

@dp.callback_query_handler(lambda c: c.data == "create_link")
async def create_link(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    link_code = secrets.token_hex(6)  # например: a7f3k9
    
    links = load_links()
    links[link_code] = user_id
    save_links(links)
    
    # Ссылка на твою страницу
    link = f"https://твой-ник.github.io/репо/?code={link_code}"
    
    await callback.message.answer(
        f"✅ Твоя ссылка готова!\n\n"
        f"🔗 {link}\n\n"
        f"📤 Отправь её человеку — и его карта придёт тебе!",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("📋 Копировать", callback_data=f"copy_{link}")
        )
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("copy_"))
async def copy_link(callback: types.CallbackQuery):
    link = callback.data.replace("copy_", "")
    await callback.answer(f"Ссылка скопирована!", show_alert=True)

# Команда для проверки статистики (только для админа)
@dp.message_handler(commands=['admin'])
async def admin_cmd(message: Message):
    if message.from_user.id == ADMIN_ID:
        links = load_links()
        await message.answer(f"📊 Всего активных ссылок: {len(links)}")

if __name__ == '__main__':
    executor.start_polling(dp)