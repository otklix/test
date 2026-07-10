import os
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import io

# ========== НАСТРОЙКИ ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== ХРАНИЛИЩЕ ==========
user_channels = {}

# ========== КЛАВИАТУРЫ ==========
def main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔍 Проверить ники", callback_data="check"),
        InlineKeyboardButton(text="🚀 Создать канал", callback_data="create")
    )
    builder.row(
        InlineKeyboardButton(text="👑 Передать права", callback_data="transfer"),
        InlineKeyboardButton(text="🖼️ Сменить аватарку", callback_data="change_avatar")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Настройки канала", callback_data="settings"),
        InlineKeyboardButton(text="🌐 Открыть сайт", url="https://otklix.github.io/wait/")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Мои каналы", callback_data="my_channels")
    )
    return builder.as_markup()

def channels_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    channels = user_channels.get(user_id, [])
    if not channels:
        builder.row(InlineKeyboardButton(text="❌ Нет каналов", callback_data="no_channels"))
    else:
        for ch in channels:
            builder.row(InlineKeyboardButton(
                text=f"📢 {ch['title']} (@{ch['username']})",
                callback_data=f"channel_{ch['channel_id']}"
            ))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data="back"))
    return builder.as_markup()

def settings_keyboard(channel_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Изменить название", callback_data=f"rename_{channel_id}"),
        InlineKeyboardButton(text="📄 Изменить описание", callback_data=f"bio_{channel_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🖼️ Сменить аватарку", callback_data=f"avatar_{channel_id}"),
        InlineKeyboardButton(text="🔗 Изменить ссылку", callback_data=f"link_{channel_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔒 Приватность", callback_data=f"privacy_{channel_id}"),
        InlineKeyboardButton(text="👑 Передать права", callback_data=f"transfer_owner_{channel_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить канал", callback_data=f"delete_{channel_id}")
    )
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data="back"))
    return builder.as_markup()

# ========== СОСТОЯНИЯ ==========
class CheckStates(StatesGroup):
    waiting_nicks = State()

class CreateStates(StatesGroup):
    waiting_username = State()

class TransferStates(StatesGroup):
    waiting_channel = State()
    waiting_new_owner = State()

class AvatarStates(StatesGroup):
    waiting_channel = State()
    waiting_photo = State()

class RenameStates(StatesGroup):
    waiting_channel = State()
    waiting_new_name = State()

class BioStates(StatesGroup):
    waiting_channel = State()
    waiting_new_bio = State()

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

# ========== АНИМАЦИЯ ПЕЧАТИ ==========
async def typing_animation(message: types.Message, text: str, delay: float = 0.06):
    msg = await message.answer("⌨️ Печатаю...")
    current_text = ""
    for char in text:
        current_text += char
        try:
            await msg.edit_text(current_text)
        except:
            pass
        await asyncio.sleep(delay)
    return msg

# ========== КОМАНДА /start ==========
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await typing_animation(
        message,
        "👋 Привет! Я бот Fint Username!\n\n"
        "Что я умею:\n"
        "🔍 Проверять ники на Fragment.com\n"
        "🚀 Создавать каналы\n"
        "👑 Передавать права\n"
        "🖼️ Менять аватарку\n"
        "⚙️ Настраивать каналы\n\n"
        "👇 Выбери действие:",
        delay=0.05
    )
    await message.answer("👇 Выбери действие:", reply_markup=main_keyboard())

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
    
    loading_msg = await message.answer("⏳ Проверяю ники на Fragment.com...")
    result = await check_nicks(nicks)
    await loading_msg.delete()
    
    free_list = "\n".join([f"@{n}" for n in result["free"][:10]])
    more = f"... и ещё {len(result['free']) - 10}" if len(result['free']) > 10 else ""
    
    result_text = (
        f"📊 <b>Результат проверки</b>\n\n"
        f"✅ Свободных: <b>{len(result['free'])}</b>\n"
        f"❌ Занятых: <b>{len(result['taken'])}</b>\n"
        f"💰 На аукционе: <b>{len(result['auction'])}</b>\n\n"
        f"📋 Свободные ники:\n{free_list} {more}"
    )
    
    await typing_animation(message, result_text, delay=0.04)
    await message.answer("✅ Готово!", reply_markup=main_keyboard())
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
                reply_markup=main_keyboard()
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
        
        user_id = message.from_user.id
        if user_id not in user_channels:
            user_channels[user_id] = []
        user_channels[user_id].append({
            "channel_id": channel.id,
            "username": username,
            "title": f"Канал @{username}",
            "created_at": datetime.now().isoformat()
        })
        
        await loading_msg.delete()
        await typing_animation(
            message,
            f"✅ <b>Канал создан!</b>\n\n"
            f"📢 Название: {channel.title}\n"
            f"🔗 Ссылка: https://t.me/{username}\n"
            f"👑 Ты владелец!\n\n"
            f"Используй настройки для управления каналом.",
            delay=0.05
        )
        await message.answer("🎉 Поздравляю!", reply_markup=main_keyboard())
    except Exception as e:
        await loading_msg.delete()
        error_msg = str(e)
        if "USERNAME_OCCUPIED" in error_msg:
            await message.answer(f"❌ Ник @{username} уже занят. Попробуй другой.", reply_markup=main_keyboard())
        else:
            await message.answer(f"❌ Ошибка: {error_msg}", reply_markup=main_keyboard())
    await state.clear()

# ========== МОИ КАНАЛЫ ==========
@dp.callback_query(F.data == "my_channels")
async def show_channels(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text(
        "📊 <b>Твои каналы</b>",
        reply_markup=channels_keyboard(user_id)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("channel_"))
async def channel_detail(callback: types.CallbackQuery):
    channel_id = int(callback.data.replace("channel_", ""))
    user_id = callback.from_user.id
    channels = user_channels.get(user_id, [])
    channel = next((c for c in channels if c["channel_id"] == channel_id), None)
    if not channel:
        await callback.message.edit_text("❌ Канал не найден.", reply_markup=main_keyboard())
        await callback.answer()
        return
    await callback.message.edit_text(
        f"📢 <b>{channel['title']}</b>\n\n"
        f"🔗 @{channel['username']}\n"
        f"📅 Создан: {channel['created_at'][:10]}\n\n"
        f"⚙️ Управление каналом:",
        reply_markup=settings_keyboard(channel_id)
    )
    await callback.answer()

# ========== НАСТРОЙКИ ==========
@dp.callback_query(F.data == "settings")
async def show_settings(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    channels = user_channels.get(user_id, [])
    if not channels:
        await callback.message.edit_text("❌ У тебя нет каналов. Создай канал через /start.", reply_markup=main_keyboard())
        await callback.answer()
        return
    await callback.message.edit_text("📢 <b>Выбери канал для настройки:</b>", reply_markup=channels_keyboard(user_id))
    await callback.answer()

# ========== ИЗМЕНЕНИЕ НАЗВАНИЯ ==========
@dp.callback_query(F.data.startswith("rename_"))
async def start_rename(callback: types.CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.replace("rename_", ""))
    await state.update_data(channel_id=channel_id)
    await callback.message.edit_text("📝 Введи новое название для канала:", reply_markup=None)
    await state.set_state(RenameStates.waiting_new_name)
    await callback.answer()

@dp.message(RenameStates.waiting_new_name)
async def process_rename(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    new_name = message.text.strip()
    try:
        await message.bot.set_chat_title(chat_id=channel_id, title=new_name)
        await message.answer(f"✅ Название канала изменено на: <b>{new_name}</b>", reply_markup=main_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=main_keyboard())
    await state.clear()

# ========== ИЗМЕНЕНИЕ ОПИСАНИЯ ==========
@dp.callback_query(F.data.startswith("bio_"))
async def start_bio(callback: types.CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.replace("bio_", ""))
    await state.update_data(channel_id=channel_id)
    await callback.message.edit_text("📄 Введи новое описание для канала:", reply_markup=None)
    await state.set_state(BioStates.waiting_new_bio)
    await callback.answer()

@dp.message(BioStates.waiting_new_bio)
async def process_bio(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    new_bio = message.text.strip()
    try:
        await message.bot.set_chat_description(chat_id=channel_id, description=new_bio)
        await message.answer(f"✅ Описание канала обновлено!", reply_markup=main_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=main_keyboard())
    await state.clear()

# ========== СМЕНА АВАТАРКИ ==========
@dp.callback_query(F.data == "change_avatar")
async def start_change_avatar(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    channels = user_channels.get(user_id, [])
    if not channels:
        await callback.message.edit_text("❌ У тебя нет каналов. Создай канал через /start.", reply_markup=main_keyboard())
        await callback.answer()
        return
    await callback.message.edit_text("📢 <b>Выбери канал для смены аватарки:</b>", reply_markup=channels_keyboard(user_id))
    await state.set_state(AvatarStates.waiting_channel)
    await callback.answer()

@dp.callback_query(F.data.startswith("avatar_"))
async def start_avatar(callback: types.CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.replace("avatar_", ""))
    await state.update_data(channel_id=channel_id)
    await callback.message.edit_text("🖼️ Отправь мне новую аватарку для канала.\nФото должно быть квадратным.", reply_markup=None)
    await state.set_state(AvatarStates.waiting_photo)
    await callback.answer()

@dp.message(AvatarStates.waiting_photo, F.photo)
async def process_avatar(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    try:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        file_data = await message.bot.download_file(file.file_path)
        await message.bot.set_chat_photo(
            chat_id=channel_id,
            photo=FSInputFile(io.BytesIO(file_data.getvalue()))
        )
        await message.answer("✅ Аватарка канала обновлена!", reply_markup=main_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=main_keyboard())
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
    await message.answer("👤 Введи @username нового владельца:")
    await state.set_state(TransferStates.waiting_new_owner)

@dp.message(TransferStates.waiting_new_owner)
async def process_transfer_owner(message: types.Message, state: FSMContext):
    new_owner = message.text.strip().replace('@', '')
    data = await state.get_data()
    channel_username = data.get('channel_username')
    loading_msg = await message.answer(f"⏳ Передаю права на @{channel_username}...")
    try:
        chat = await message.bot.get_chat(f"@{channel_username}")
        try:
            new_owner_user = await message.bot.get_chat(f"@{new_owner}")
            new_owner_id = new_owner_user.id
        except:
            await loading_msg.delete()
            await message.answer(f"❌ Пользователь @{new_owner} не найден.", reply_markup=main_keyboard())
            await state.clear()
            return
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
        await message.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=new_owner_id,
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
            f"✅ <b>Права переданы!</b>\n\n"
            f"📢 Канал: @{channel_username}\n"
            f"👤 Новый владелец: @{new_owner}",
            delay=0.05
        )
        await message.answer("🔑 Бот вышел из канала.", reply_markup=main_keyboard())
        await message.bot.leave_chat(chat.id)
    except Exception as e:
        await loading_msg.delete()
        await message.answer(
            f"❌ Ошибка: {str(e)}\n"
            f"Убедись, что канал @{channel_username} существует и бот является админом.",
            reply_markup=main_keyboard()
        )
    await state.clear()

# ========== КНОПКА НАЗАД ==========
@dp.callback_query(F.data == "back")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("👋 Главное меню:", reply_markup=main_keyboard())
    await callback.answer()

# ========== НЕИЗВЕСТНЫЕ КОМАНДЫ ==========
@dp.message()
async def unknown_command(message: types.Message):
    await message.answer(
        "❓ Неизвестная команда.\n"
        "Используй /start для главного меню."
    )

# ========== ЗАПУСК ==========
async def main():
    logger.info("🤖 Бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())