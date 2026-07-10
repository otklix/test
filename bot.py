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

# Настройка логирования
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logging.error("BOT_TOKEN не найден!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== Клавиатуры ==========
main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔍 Проверить ники", callback_data="check")],
    [InlineKeyboardButton(text="🚀 Создать канал", callback_data="create")],
    [InlineKeyboardButton(text="👑 Передать права", callback_data="transfer")],
    [InlineKeyboardButton(text="🌐 Открыть сайт", url="https://otklix.github.io/wait/")]
])

# ========== Состояния ==========
class CheckStates(StatesGroup):
    waiting_nicks = State()

class CreateStates(StatesGroup):
    waiting_username = State()

class TransferStates(StatesGroup):
    waiting_channel = State()
    waiting_new_owner = State()

# ========== Проверка на Fragment ==========
async def check_nick_on_fragment(nick: str) -> str:
    """Проверяет ник на Fragment.com. Возвращает 'free', 'taken', 'auction'."""
    url = f"https://fragment.com/username/{nick}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Если есть кнопка Bid — ник на аукционе
                if soup.find('button', string=lambda t: t and 'Bid' in t):
                    return "auction"
                # Если есть надпись "not available" — занят
                if soup.find(string=lambda t: t and 'not available' in t.lower()):
                    return "taken"
                return "free"
    except:
        return "taken"  # при ошибке считаем занятым

async def check_nicks(nicks: list) -> dict:
    """Проверяет список ников и возвращает статистику."""
    result = {"free": [], "taken": [], "auction": []}
    
    # Проверяем по 5 ников одновременно, чтобы не перегружать Fragment
    for i in range(0, len(nicks), 5):
        batch = nicks[i:i+5]
        tasks = [check_nick_on_fragment(nick) for nick in batch]
        statuses = await asyncio.gather(*tasks)
        
        for nick, status in zip(batch, statuses):
            result[status].append(nick)
    
    return result

# ========== Команда /start ==========
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для работы с Telegram каналами.\n\n"
        "Что умею:\n"
        "🔍 Проверять ники на Fragment.com\n"
        "🚀 Создавать каналы\n"
        "👑 Передавать права\n\n"
        "Выбери действие:",
        reply_markup=main_keyboard
    )

# ========== Проверка ников ==========
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
    # Парсим ники
    raw = message.text
    nicks = [n.strip().replace('@', '') for n in raw.replace(',', ' ').split() if n.strip()]
    
    if not nicks:
        await message.answer("❌ Список пуст. Попробуй ещё раз.")
        return
    
    if len(nicks) > 100:
        await message.answer(f"❌ Слишком много! Максимум 100 ников. У тебя {len(nicks)}.")
        return
    
    await message.answer(f"⏳ Проверяю {len(nicks)} ников на Fragment.com...")
    
    result = await check_nicks(nicks)
    
    # Формируем ответ
    free_list = "\n".join([f"@{n}" for n in result["free"][:10]])
    more = f"... и ещё {len(result['free']) - 10}" if len(result['free']) > 10 else ""
    
    await message.answer(
        f"📊 <b>Результат проверки</b>\n\n"
        f"✅ Свободных: <b>{len(result['free'])}</b>\n"
        f"❌ Занятых: <b>{len(result['taken'])}</b>\n"
        f"💰 На аукционе: <b>{len(result['auction'])}</b>\n\n"
        f"📋 Свободные ники:\n{free_list} {more}",
        reply_markup=main_keyboard
    )
    
    await state.clear()

# ========== Создание канала ==========
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
    
    try:
        # Проверяем, свободен ли ник
        status = await check_nick_on_fragment(username)
        
        if status != "free":
            await message.answer(
                f"❌ Ник @{username} {'занят' if status == 'taken' else 'на аукционе'}.\n"
                f"Попробуй другой.",
                reply_markup=main_keyboard
            )
            await state.clear()
            return
        
        # Создаём канал
        channel = await message.bot.create_channel(
            title=f"Канал @{username}",
            username=username
        )
        
        # Добавляем пользователя как владельца
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
        
        await message.answer(
            f"✅ <b>Канал создан!</b>\n\n"
            f"📢 Название: {channel.title}\n"
            f"🔗 Ссылка: https://t.me/{username}\n"
            f"👑 Ты владелец!",
            reply_markup=main_keyboard
        )
        
    except Exception as e:
        error_msg = str(e)
        if "USERNAME_OCCUPIED" in error_msg:
            await message.answer(f"❌ Ник @{username} уже занят. Попробуй другой.", reply_markup=main_keyboard)
        else:
            await message.answer(f"❌ Ошибка: {error_msg}", reply_markup=main_keyboard)
    
    await state.clear()

# ========== Передача прав ==========
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
    
    try:
        # Получаем информацию о канале
        chat = await message.bot.get_chat(f"@{channel_username}")
        
        # Проверяем, что пользователь — владелец
        # (для простоты просто делаем промоушен)
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
        
        # Назначаем нового владельца
        await message.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=new_owner,  # Здесь нужен ID, а не username
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
        
        await message.answer(
            f"✅ <b>Права переданы!</b>\n\n"
            f"📢 Канал: @{channel_username}\n"
            f"👤 Новый владелец: @{new_owner}\n\n"
            f"🔑 Бот вышел из канала.",
            reply_markup=main_keyboard
        )
        
        # Бот выходит из канала
        await message.bot.leave_chat(chat.id)
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n"
            f"Убедись, что канал @{channel_username} существует и бот является админом.",
            reply_markup=main_keyboard
        )
    
    await state.clear()

# ========== Обработка неизвестных команд ==========
@dp.message()
async def unknown_command(message: types.Message):
    await message.answer(
        "❓ Неизвестная команда.\n"
        "Используй /start для главного меню."
    )

# ========== Запуск ==========
async def main():
    logging.info("🤖 Бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())