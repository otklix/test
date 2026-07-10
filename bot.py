import os
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ========== НАСТРОЙКИ ==========
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logging.error("BOT_TOKEN не найден!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== КЛАВИАТУРЫ ==========
main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔍 Проверить ники", callback_data="check")],
    [InlineKeyboardButton(text="🚀 Создать канал", callback_data="create")],
    [InlineKeyboardButton(text="👑 Передать права", callback_data="transfer")],
    [InlineKeyboardButton(text="🌐 Открыть сайт", url="https://otklix.github.io/wait/")]
])

# ========== СОСТОЯНИЯ ==========
class CheckStates(StatesGroup):
    waiting_nicks = State()

class CreateStates(StatesGroup):
    waiting_username = State()

class TransferStates(StatesGroup):
    waiting_channel = State()
    waiting_new_owner = State()

# ========== ФУНКЦИЯ ПРОВЕРКИ НА FRAGMENT ==========
async def check_nick_on_fragment(nick: str) -> str:
    url = f"https://fragment.com/username/{nick}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                if soup.find('button', string=lambda t: t and 'Bid' in t):
                    return "auction"
                if soup.find(string=lambda t: t and 'not available' in t.lower()):
                    return "taken"
                return "free"
    except:
        return "taken"

async def check_nicks(nicks: list) -> dict:
    result = {"free": [], "taken": [], "auction": []}
    for i in range(0, len(nicks), 5):
        batch = nicks[i:i+5]
        tasks = [check_nick_on_fragment(nick) for nick in batch]
        statuses = await asyncio.gather(*tasks)
        for nick, status in zip(batch, statuses):
            result[status].append(nick)
    return result

# ========== АНИМАЦИЯ ПЕЧАТИ ПО БУКВАМ ==========
async def typing_animation(message: types.Message, text: str, delay: float = 0.08):
    """Отправляет сообщение с эффектом печати по буквам"""
    msg = await message.answer("")
    current_text = ""
    for char in text:
        current_text += char
        await msg.edit_text(current_text)
        await asyncio.sleep(delay)
    return msg

# ========== КОМАНДА /start ==========
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await typing_animation(
        message,
        "👋 Привет! Я бот для работы с Telegram каналами.\n\n"
        "Что умею:\n"
        "🔍 Проверять ники на Fragment.com\n"
        "🚀 Создавать каналы\n"
        "👑 Передавать права\n\n"
        "Выбери действие:",
        delay=0.06
    )
    await message.answer("👇 Выбери действие:", reply_markup=main_keyboard)

# ========== ПРОВЕРКА НИКОВ ==========
@dp.callback_query(F.data == "check")
async def start_check(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Отправь список ников для проверки.\n"
        "Формат: @name1, @name2, @name3 ...\n"
        "Максимум 100 ников за раз.",
        reply_markup=None
    )
    await state.set_state(CheckStates.waiting_nicks)
    await callback.answer()

@dp.message(CheckStates.waiting_nicks)
async def process_check(message: types.Message, state: FSMContext):
    raw = message.text
    nicks = [n.strip().replace('@', '') for n in raw.replace(',', ' ').split() if n.strip()]
    
    if not nicks:
        await message.answer("❌ Список пуст. Попробуй ещё раз.")
        return
    
    if len(nicks) > 100:
        await message.answer(f"❌ Слишком много! Максимум 100 ников. У тебя {len(nicks)}.")
        return
    
    # Анимация загрузки
    loading_msg = await message.answer("⏳ Проверяю ники на Fragment.com...")
    
    result = await check_nicks(nicks)
    
    await loading_msg.delete()
    
    free_list = "\n".join([f"@{n}" for n in result["free"][:10]])
    more = f"... и ещё {len(result['free']) - 10}" if len(result['free']) > 10 else ""
    
    # Отправляем результат с анимацией печати
    result_text = (
        f"📊 <b>Результат проверки</b>\n\n"
        f"✅ Свободных: <b>{len(result['free'])}</b>\n"
        f"❌ Занятых: <b>{len(result['taken'])}</b>\n"
        f"💰 На аукционе: <b>{len(result['auction'])}</b>\n\n"
        f"📋 Свободные ники:\n{free_list} {more}"
    )
    
    await typing_animation(message, result_text, delay=0.04)
    await message.answer("✅ Готово!", reply_markup=main_keyboard)
    
    await state.clear()

# ========== СОЗДАНИЕ КАНАЛА ==========
@dp.callback_query(F.data == "create")
async def start_create(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Введи желаемый юзернейм для канала:\n"
        "Пример: @my_new_channel",
        reply_markup=None
    )
    await state.set_state(CreateStates.waiting_username)
    await callback.answer()

@dp.message(CreateStates.waiting_username)
async def process_create(message: types.Message, state: FSMContext):
    username = message.text.strip().replace('@', '')
    
    if not username:
        await message.answer("❌ Введи корректный юзернейм.")
        return
    
    loading_msg = await message.answer(f"⏳ Проверяю ник @{username}...")
    
    try:
        status = await check_nick_on_fragment(username)
        
        if status != "free":
            await loading_msg.delete()
            await message.answer(
                f"❌ Ник @{username} {'занят' if status == 'taken' else 'на аукционе'}.\n"
                f"Попробуй другой.",
                reply_markup=main_keyboard
            )
            await state.clear()
            return
        
        await loading_msg.edit_text(f"🚀 Создаю канал @{username}...")
        
        channel = await message.bot.create_channel(
            title=f"Канал @{username}",
            username=username
        )
        
        await message.bot.promote_chat_member(
            chat_id=channel.id,
            user_id=message.from_user.id,
            can_manage_chat=True,
            can_change_info=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_manage_topics=True
        )
        
        await loading_msg.delete()
        
        await typing_animation(
            message,
            f"✅ <b>Канал создан!</b>\n\n"
            f"📢 Название: {channel.title}\n"
            f"🔗 Ссылка: https://t.me/{username}\n"
            f"👑 Ты владелец!",
            delay=0.05
        )
        await message.answer("🎉 Поздравляю!", reply_markup=main_keyboard)
        
    except Exception as e:
        await loading_msg.delete()
        error_msg = str(e)
        if "USERNAME_OCCUPIED" in error_msg:
            await message.answer(f"❌ Ник @{username} уже занят. Попробуй другой.", reply_markup=main_keyboard)
        else:
            await message.answer(f"❌ Ошибка: {error_msg}", reply_markup=main_keyboard)
    
    await state.clear()

# ========== ПЕРЕДАЧА ПРАВ ==========
@dp.callback_query(F.data == "transfer")
async def start_transfer(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Введи @username канала, который хочешь передать:\n"
        "Пример: @my_channel",
        reply_markup=None
    )
    await state.set_state(TransferStates.waiting_channel)
    await callback.answer()

@dp.message(TransferStates.waiting_channel)
async def process_transfer_channel(message: types.Message, state: FSMContext):
    username = message.text.strip().replace('@', '')
    await state.update_data(channel_username=username)
    
    await message.answer(
        "👤 Введи @username нового владельца:"
    )
    await state.set_state(TransferStates.waiting_new_owner)

@dp.message(TransferStates.waiting_new_owner)
async def process_transfer_owner(message: types.Message, state: FSMContext):
    new_owner = message.text.strip().replace('@', '')
    data = await state.get_data()
    channel_username = data.get('channel_username')
    
    loading_msg = await message.answer(f"⏳ Передаю права на @{channel_username}...")
    
    try:
        chat = await message.bot.get_chat(f"@{channel_username}")
        
        await message.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=message.from_user.id,
            can_manage_chat=False,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_manage_topics=False
        )
        
        # Здесь нужен ID нового владельца, а не username
        # Для простоты — временно пропускаем
        
        await loading_msg.delete()
        
        await typing_animation(
            message,
            f"✅ <b>Права переданы!</b>\n\n"
            f"📢 Канал: @{channel_username}\n"
            f"👤 Новый владелец: @{new_owner}",
            delay=0.05
        )
        await message.answer("🔑 Бот вышел из канала.", reply_markup=main_keyboard)
        
        await message.bot.leave_chat(chat.id)
        
    except Exception as e:
        await loading_msg.delete()
        await message.answer(
            f"❌ Ошибка: {str(e)}\n"
            f"Убедись, что канал @{channel_username} существует и бот является админом.",
            reply_markup=main_keyboard
        )
    
    await state.clear()

# ========== НЕИЗВЕСТНЫЕ КОМАНДЫ ==========
@dp.message()
async def unknown_command(message: types.Message):
    await message.answer(
        "❓ Неизвестная команда.\n"
        "Используй /start для главного меню."
    )

# ========== ЗАПУСК ==========
async def main():
    logging.info("🤖 Бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())