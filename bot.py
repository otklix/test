import os
import asyncio
import random
import string
import aiohttp
import zipfile
import io
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = "ВАШ_ТОКЕН_БОТА"

REPORTS_DIR = "reports"
IMAGES_DIR = "images"
ZIP_DIR = "zips"
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(ZIP_DIR, exist_ok=True)

MAX_ATTEMPTS = 50
TIMEOUT = 0.3

# ===== ИНИЦИАЛИЗАЦИЯ БОТА =====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

class SearchStates(StatesGroup):
    waiting_for_username = State()

# Хранилище найденных юзернеймов
found_usernames = []
stats = {
    "total": 0,
    "valid": 0,
    "invalid": 0,
    "banned": 0
}

# ===== СОЗДАНИЕ ПРОГРЕСС-БАРА (как на IMG_8461) =====
def create_progress_image(progress: int, total: int, username: str = "", status: str = "Поиск") -> bytes:
    """Создаёт стильный прогресс-бар как в Aqua Checker"""
    width, height = 800, 400
    percent = (progress / total) * 100 if total > 0 else 0
    
    img = Image.new('RGB', (width, height), color=(10, 10, 30))
    draw = ImageDraw.Draw(img)
    
    # Градиентный фон
    for i in range(height):
        r = 10 + int(i * 0.03)
        g = 10 + int(i * 0.02)
        b = 30 + int(i * 0.08)
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_progress = ImageFont.truetype("arial.ttf", 28)
        font_username = ImageFont.truetype("arial.ttf", 22)
        font_status = ImageFont.truetype("arial.ttf", 20)
        font_sub = ImageFont.truetype("arial.ttf", 16)
    except:
        font_title = ImageFont.load_default()
        font_progress = ImageFont.load_default()
        font_username = ImageFont.load_default()
        font_status = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    
    # Логотип "AQUA CHECKER" стиль
    draw.text((width//2 - 150, 20), "🔍 AQUA CHECKER", fill=(0, 200, 255), font=font_title)
    draw.text((width//2 - 80, 65), "БОТ", fill=(100, 200, 255), font=font_sub)
    
    # Заголовок статуса
    status_text = "ПОИСК ЮЗЕРНЕЙМОВ" if status == "Поиск" else "ЗАВЕРШЕНО"
    draw.text((width//2 - 120, 110), status_text, fill=(255, 255, 255), font=font_progress)
    
    # Рамка прогресс-бара
    bar_x, bar_y, bar_w, bar_h = 50, 160, width - 100, 40
    draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], 
                   outline=(0, 200, 255), width=2, fill=(20, 20, 50))
    
    # Заливка прогресса (градиент)
    fill_width = int((bar_w - 4) * (percent / 100))
    if fill_width > 0:
        for i in range(fill_width):
            ratio = i / fill_width
            r = int(0 + ratio * 0)
            g = int(150 + ratio * 50)
            b = int(200 + ratio * 55)
            draw.line([(bar_x + 2 + i, bar_y + 2), (bar_x + 2 + i, bar_y + bar_h - 2)], 
                     fill=(r, g, b), width=1)
    
    # Проценты
    percent_text = f"{percent:.1f}%"
    draw.text((width//2 - 40, 215), percent_text, fill=(0, 200, 255), font=font_progress)
    
    # Прогресс текст
    progress_text = f"{progress} / {total}"
    draw.text((width//2 - 50, 260), progress_text, fill=(150, 200, 255), font=font_username)
    
    # Имя юзернейма
    if username:
        draw.text((50, 310), f"🎯 ТЕКУЩИЙ: @{username}", fill=(100, 255, 150), font=font_username)
    
    # Статус
    status_colors = {
        "Поиск": (0, 200, 255),
        "Найден": (0, 255, 100),
        "Занят": (255, 150, 50),
        "Ошибка": (255, 50, 50)
    }
    color = status_colors.get(status, (200, 200, 200))
    draw.text((width - 250, 310), f"СТАТУС: {status.upper()}", fill=color, font=font_status)
    
    # Декоративная линия внизу
    draw.line([(50, 370), (width - 50, 370)], fill=(0, 200, 255), width=1)
    draw.text((width//2 - 100, 380), "AQUA CHECKER • v1.0", fill=(50, 100, 150), font=font_sub)
    
    # Сохраняем в байты
    img_path = os.path.join(IMAGES_DIR, f"progress_{progress}_{datetime.now().timestamp()}.png")
    img.save(img_path)
    
    with open(img_path, 'rb') as f:
        image_data = f.read()
    
    os.remove(img_path)
    return image_data

# ===== СОЗДАНИЕ HTML-ОТЧЁТА (как на IMG_8462-8464) =====
def create_report_html(username: str, stats_data: dict = None) -> str:
    """Создаёт детальный HTML-отчёт как в Aqua Checker"""
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    telegram_link = f"https://t.me/{username}"
    
    if stats_data is None:
        stats_data = {
            "valid": True,
            "donate": random.randint(1000, 100000),
            "balance": random.randint(0, 1000),
            "rap": random.randint(100, 5000),
            "groups": random.randint(0, 10),
            "followers": random.randint(0, 500),
            "badges": random.randint(0, 50),
            "premium": random.choice([True, False]),
            "two_fa": random.choice([True, False]),
            "email": random.choice([True, False])
        }
    
    status_color = "#4CAF50" if stats_data.get("valid", True) else "#f44336"
    status_text = "VALID" if stats_data.get("valid", True) else "INVALID"
    
    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@{username} — отчёт</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        @keyframes gradient {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.02); }}
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 50%, #0a0a1a 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            animation: gradient 15s ease infinite;
            background-size: 400% 400%;
        }}
        
        .container {{
            background: rgba(20, 20, 50, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 30px 80px rgba(0, 200, 255, 0.1);
            animation: slideIn 0.8s ease-out;
            border: 1px solid rgba(0, 200, 255, 0.1);
        }}
        
        .header {{
            text-align: center;
            border-bottom: 1px solid rgba(0, 200, 255, 0.1);
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        
        .logo {{
            color: #00ccff;
            font-size: 24px;
            font-weight: 800;
            letter-spacing: 2px;
        }}
        
        .logo span {{
            color: #ffffff;
        }}
        
        .username {{
            font-size: 36px;
            font-weight: 900;
            color: #00ccff;
            margin: 10px 0;
        }}
        
        .username a {{
            color: #00ccff;
            text-decoration: none;
        }}
        
        .status {{
            display: inline-block;
            padding: 5px 20px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 14px;
            background: {status_color};
            color: white;
            margin: 10px 0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin: 20px 0;
        }}
        
        .stat-card {{
            background: rgba(0, 200, 255, 0.05);
            padding: 15px;
            border-radius: 12px;
            border: 1px solid rgba(0, 200, 255, 0.08);
            transition: all 0.3s;
        }}
        
        .stat-card:hover {{
            transform: scale(1.02);
            background: rgba(0, 200, 255, 0.1);
        }}
        
        .stat-card .label {{
            font-size: 11px;
            color: #6688aa;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}
        
        .stat-card .value {{
            font-size: 20px;
            font-weight: 700;
            color: #00ccff;
            margin-top: 5px;
        }}
        
        .stat-card .value.green {{ color: #4CAF50; }}
        .stat-card .value.gold {{ color: #FFD700; }}
        .stat-card .value.purple {{ color: #9B59B6; }}
        
        .progress-bar {{
            background: rgba(0, 200, 255, 0.1);
            border-radius: 10px;
            height: 20px;
            margin: 10px 0;
            overflow: hidden;
            border: 1px solid rgba(0, 200, 255, 0.1);
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #00ccff, #0066ff);
            border-radius: 10px;
            transition: width 1s;
            width: {random.randint(30, 100)}%;
        }}
        
        .btn {{
            display: inline-block;
            background: linear-gradient(135deg, #00ccff, #0066ff);
            color: white;
            padding: 14px 30px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 700;
            font-size: 16px;
            transition: all 0.3s;
            width: 100%;
            text-align: center;
            margin-top: 15px;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 200, 255, 0.3);
        }}
        
        .footer {{
            text-align: center;
            color: #446688;
            font-size: 11px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(0, 200, 255, 0.05);
        }}
        
        .badge {{
            display: inline-block;
            background: rgba(0, 200, 255, 0.1);
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 11px;
            color: #00ccff;
            margin: 2px;
        }}
        
        @media (max-width: 480px) {{
            .container {{ padding: 20px; }}
            .stats-grid {{ grid-template-columns: 1fr; }}
            .username {{ font-size: 28px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">AQUA <span>CHECKER</span></div>
            <div class="username">
                <a href="{telegram_link}" target="_blank">@{username}</a>
            </div>
            <div class="status">{status_text}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">💰 ДОНАТ</div>
                <div class="value">{stats_data.get('donate', 0):,} R$</div>
            </div>
            <div class="stat-card">
                <div class="label">💳 БАЛАНС</div>
                <div class="value gold">{stats_data.get('balance', 0)} R$</div>
            </div>
            <div class="stat-card">
                <div class="label">📊 RAP</div>
                <div class="value purple">{stats_data.get('rap', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="label">👥 ГРУППЫ</div>
                <div class="value">{stats_data.get('groups', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="label">👤 ПОДПИСЧИКИ</div>
                <div class="value">{stats_data.get('followers', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="label">🏅 БЕЙДЖИ</div>
                <div class="value">{stats_data.get('badges', 0)}</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        
        <div style="display:flex; gap:8px; flex-wrap:wrap; justify-content:center; margin:10px 0;">
            <span class="badge">{'⭐ PREMIUM' if stats_data.get('premium', False) else ''}</span>
            <span class="badge">{'🔐 2FA' if stats_data.get('two_fa', False) else ''}</span>
            <span class="badge">{'📧 С ПОЧТОЙ' if stats_data.get('email', False) else ''}</span>
        </div>
        
        <a href="{telegram_link}" target="_blank" class="btn">🚀 ПЕРЕЙТИ В TELEGRAM</a>
        
        <div class="footer">
            AQUA CHECKER • Отчёт сгенерирован {now}
        </div>
    </div>
</body>
</html>'''

# ===== СОЗДАНИЕ ГЛАВНОЙ СТРАНИЦЫ СО СТАТИСТИКОЙ =====
def create_index_html():
    """Создаёт главную страницу со статистикой как на IMG_8462"""
    total = len(found_usernames)
    valid = sum(1 for u in found_usernames if u.get("valid", True))
    invalid = total - valid
    
    reports_list = ""
    for u in found_usernames[-20:]:
        username = u.get("username", "unknown")
        reports_list += f'<a href="reports/{username}.html">@{username}</a>\n'
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AQUA CHECKER — Статистика</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        @keyframes gradient {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        
        @keyframes slideUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.05); opacity: 0.8; }}
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 50%, #0a0a1a 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            animation: gradient 15s ease infinite;
            background-size: 400% 400%;
        }}
        
        .container {{
            background: rgba(20, 20, 50, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            max-width: 700px;
            width: 100%;
            box-shadow: 0 30px 80px rgba(0, 200, 255, 0.1);
            animation: slideUp 0.8s ease-out;
            border: 1px solid rgba(0, 200, 255, 0.1);
        }}
        
        .header {{
            text-align: center;
            border-bottom: 1px solid rgba(0, 200, 255, 0.1);
            padding-bottom: 20px;
        }}
        
        .logo {{
            color: #00ccff;
            font-size: 28px;
            font-weight: 900;
            letter-spacing: 3px;
        }}
        
        .logo span {{ color: #ffffff; }}
        
        .subtitle {{
            color: #6688aa;
            font-size: 14px;
            margin-top: 5px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 15px;
            margin: 25px 0;
        }}
        
        .stat-box {{
            background: rgba(0, 200, 255, 0.05);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid rgba(0, 200, 255, 0.08);
            transition: all 0.3s;
        }}
        
        .stat-box:hover {{ transform: scale(1.05); }}
        
        .stat-box .number {{
            font-size: 28px;
            font-weight: 800;
            color: #00ccff;
        }}
        
        .stat-box .number.green {{ color: #4CAF50; }}
        .stat-box .number.red {{ color: #f44336; }}
        .stat-box .number.gold {{ color: #FFD700; }}
        
        .stat-box .label {{
            font-size: 11px;
            color: #6688aa;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 5px;
        }}
        
        .progress-section {{
            margin: 20px 0;
        }}
        
        .progress-bar {{
            background: rgba(0, 200, 255, 0.05);
            border-radius: 10px;
            height: 25px;
            overflow: hidden;
            border: 1px solid rgba(0, 200, 255, 0.1);
            margin: 5px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #00ccff, #0066ff);
            border-radius: 10px;
            transition: width 1s;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .progress-fill.green {{ background: linear-gradient(90deg, #4CAF50, #45a049); }}
        .progress-fill.gold {{ background: linear-gradient(90deg, #FFD700, #f57c00); }}
        .progress-fill.purple {{ background: linear-gradient(90deg, #9B59B6, #8e44ad); }}
        
        .recent {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(0, 200, 255, 0.05);
        }}
        
        .recent a {{
            color: #00ccff;
            text-decoration: none;
            display: inline-block;
            margin: 4px 6px;
            padding: 4px 12px;
            background: rgba(0, 200, 255, 0.05);
            border-radius: 15px;
            font-size: 13px;
            transition: all 0.3s;
            border: 1px solid rgba(0, 200, 255, 0.05);
        }}
        
        .recent a:hover {{
            background: rgba(0, 200, 255, 0.15);
            transform: scale(1.05);
        }}
        
        .btn {{
            display: inline-block;
            background: linear-gradient(135deg, #00ccff, #0066ff);
            color: white;
            padding: 14px 30px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 700;
            font-size: 16px;
            transition: all 0.3s;
            width: 100%;
            text-align: center;
            margin-top: 15px;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 200, 255, 0.3);
        }}
        
        .footer {{
            text-align: center;
            color: #446688;
            font-size: 11px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(0, 200, 255, 0.05);
        }}
        
        @media (max-width: 480px) {{
            .container {{ padding: 20px; }}
            .stats-grid {{ grid-template-columns: 1fr 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">AQUA <span>CHECKER</span></div>
            <div class="subtitle">GLOBAL STATISTICS</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-box">
                <div class="number">{total}</div>
                <div class="label">TOTAL</div>
            </div>
            <div class="stat-box">
                <div class="number green">{valid}</div>
                <div class="label">VALID</div>
            </div>
            <div class="stat-box">
                <div class="number red">{invalid}</div>
                <div class="label">INVALID</div>
            </div>
            <div class="stat-box">
                <div class="number gold">0</div>
                <div class="label">BANNED</div>
            </div>
        </div>
        
        <div class="progress-section">
            <div class="progress-bar">
                <div class="progress-fill green" style="width:{ (valid/total*100) if total > 0 else 0 }%;">
                    { (valid/total*100) if total > 0 else 0 :.0f}%
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; color:#6688aa; font-size:12px;">
                <span>✅ VALID {valid}</span>
                <span>❌ INVALID {invalid}</span>
            </div>
        </div>
        
        <div class="recent">
            <div style="color:#00ccff; font-weight:600; margin-bottom:10px;">📋 ПОСЛЕДНИЕ НАЙДЕННЫЕ:</div>
            <div>
                {reports_list if reports_list else '<span style="color:#446688;">Пока нет найденных юзернеймов</span>'}
            </div>
        </div>
        
        <a href="https://t.me/ваш_бот" target="_blank" class="btn">🚀 ЗАПУСТИТЬ БОТА</a>
        
        <div class="footer">
            AQUA CHECKER • v1.0 • {datetime.now().strftime("%d.%m.%Y")}
        </div>
    </div>
</body>
</html>'''

    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(html)
    return "index.html"

# ===== СОЗДАНИЕ ZIP-АРХИВА =====
def create_zip_archive() -> bytes:
    """Создаёт ZIP-архив со всеми отчётами"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Добавляем все HTML-отчёты
        for filename in os.listdir(REPORTS_DIR):
            if filename.endswith('.html'):
                filepath = os.path.join(REPORTS_DIR, filename)
                zip_file.write(filepath, f"reports/{filename}")
        
        # Добавляем index.html
        if os.path.exists("index.html"):
            zip_file.write("index.html", "index.html")
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# ===== ОСНОВНЫЕ ОБРАБОТЧИКИ =====
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🌊 **AQUA CHECKER**\n\n"
        "🔍 Я ищу свободные 5-символьные юзернеймы в Telegram!\n\n"
        "📌 **Как работать:**\n"
        "• Напиши юзернейм (например, `abcdx`)\n"
        "• Или используй маску: `a****`\n"
        "• Я проверю и создам красивый отчёт\n\n"
        "📊 **Статистика:**\n"
        f"• Найдено: {len(found_usernames)}\n"
        f"• Валидных: {stats['valid']}\n\n"
        "✨ **Попробуй прямо сейчас!**",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Начать поиск", callback_data="start_search")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton(text="📦 Скачать ZIP", callback_data="download_zip")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
        ])
    )

@router.callback_query(F.data == "start_search")
async def start_search(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "✏️ **Напиши юзернейм или маску:**\n\n"
        "• `abcdx` — конкретный юзернейм\n"
        "• `a****` — все на 'a'\n"
        "• `ab***` — начинается на 'ab'\n\n"
        "⏳ Минимум 5 символов!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
        ])
    )
    await state.set_state(SearchStates.waiting_for_username)
    await callback.answer()

@router.message(SearchStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    username = message.text.strip().lower().replace('@', '').strip()
    
    if len(username) < 5:
        await message.answer("❌ Минимум 5 символов!")
        return
    
    if not all(c.isalnum() or c == '_' or c == '*' for c in username):
        await message.answer("❌ Только латиница, цифры, '_' и '*' !")
        return
    
    await message.answer(f"🔍 Ищу **@{username}**...", parse_mode="Markdown")
    
    is_available = await check_username(username)
    
    if is_available:
        await generate_report(username, message)
    else:
        await message.answer(f"❌ **@{username}** занят!\n\n🔍 Ищу похожие варианты...", parse_mode="Markdown")
        await search_similar(username, message)
    
    await state.clear()

async def check_username(username: str) -> bool:
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/checkUsername"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"username": username}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("result", False)
                return False
    except:
        return False

async def search_similar(pattern: str, message: Message):
    status_msg = await message.answer("🔄 Начинаю поиск...")
    
    found = False
    total = MAX_ATTEMPTS
    
    for i in range(total):
        if '*' in pattern:
            new_username = generate_from_pattern(pattern)
        else:
            new_username = generate_random()
        
        if i % 3 == 0:
            progress_img = create_progress_image(i, total, new_username, "Поиск")
            photo = BufferedInputFile(progress_img, filename="progress.png")
            await status_msg.delete()
            status_msg = await message.answer_photo(photo, caption=f"🔍 Поиск: {i}/{total}")
        
        is_available = await check_username(new_username)
        
        if is_available:
            await status_msg.delete()
            await generate_report(new_username, message)
            found = True
            break
        
        await asyncio.sleep(TIMEOUT)
    
    if not found:
        await status_msg.delete()
        await message.answer("😔 Не удалось найти свободный юзернейм.")

def generate_from_pattern(pattern: str) -> str:
    result = []
    chars = string.ascii_lowercase + string.digits
    for c in pattern:
        if c == '*':
            result.append(random.choice(chars))
        else:
            result.append(c)
    return ''.join(result)

def generate_random() -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=5))

async def generate_report(username: str, message: Message):
    """Генерирует отчёт и обновляет статистику"""
    # Генерируем случайные метрики (как в Aqua Checker)
    stats_data = {
        "valid": True,
        "donate": random.randint(1000, 150000),
        "balance": random.randint(0, 5000),
        "rap": random.randint(100, 10000),
        "groups": random.randint(0, 15),
        "followers": random.randint(0, 1000),
        "badges": random.randint(0, 100),
        "premium": random.choice([True, False]),
        "two_fa": random.choice([True, False]),
        "email": random.choice([True, False])
    }
    
    # Сохраняем в список
    found_usernames.append({"username": username, **stats_data})
    stats["total"] += 1
    stats["valid"] += 1
    
    # Создаём HTML
    html_content = create_report_html(username, stats_data)
    filepath = os.path.join(REPORTS_DIR, f"{username}.html")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Обновляем index.html
    create_index_html()
    
    # Создаём прогресс-бар "Завершено"
    done_img = create_progress_image(100, 100, username, "Найден")
    photo = BufferedInputFile(done_img, filename="done.png")
    
    await message.answer_photo(
        photo,
        caption=f"✅ **Юзернейм найден!**\n\n"
                f"📌 **@{username}** — СВОБОДЕН!\n"
                f"🔗 Ссылка: https://t.me/{username}\n"
                f"📁 Отчёт: `{filepath}`\n\n"
                f"📊 Всего найдено: {stats['total']}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Перейти", url=f"https://t.me/{username}")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton(text="🔍 Искать ещё", callback_data="start_search")]
        ])
    )

@router.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    total = stats["total"]
    valid = stats["valid"]
    invalid = stats["invalid"]
    
    await callback.message.answer(
        f"📊 **СТАТИСТИКА AQUA CHECKER**\n\n"
        f"✅ **Всего проверено:** {total}\n"
        f"✅ **Валидных:** {valid}\n"
        f"❌ **Невалидных:** {invalid}\n"
        f"🚫 **Забаненных:** 0\n\n"
        f"📈 **Валидность:** { (valid/total*100) if total > 0 else 0 :.1f}%\n\n"
        f"📁 Открой `index.html` для полной статистики!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Скачать ZIP", callback_data="download_zip")],
            [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="start_search")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "download_zip")
async def download_zip(callback: CallbackQuery):
    if len(found_usernames) == 0:
        await callback.message.answer("📭 Нет отчётов для скачивания!")
        await callback.answer()
        return
    
    await callback.message.answer("📦 Создаю ZIP-архив...")
    
    zip_data = create_zip_archive()
    zip_file = BufferedInputFile(zip_data, filename=f"reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
    
    await callback.message.answer_document(
        zip_file,
        caption=f"📦 **ZIP-архив с отчётами**\n\n"
                f"📄 Файлов: {len(found_usernames)}\n"
                f"📅 Создан: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "help")
async def help_cmd(callback: CallbackQuery):
    await callback.message.answer(
        "📚 **Помощь AQUA CHECKER**\n\n"
        "🔹 **Команды:**\n"
        "/start — Главное меню\n"
        "Напиши юзернейм — начать поиск\n\n"
        "🔹 **Маска:**\n"
        "`a****` — найдет все на 'a'\n"
        "`ab***` — начинается на 'ab'\n\n"
        "🔹 **Функции:**\n"
        "📊 Статистика — просмотр результатов\n"
        "📦 ZIP — скачать все отчёты\n\n"
        "🔹 **Ограничения:**\n"
        "• 5+ символов\n"
        "• Только латиница, цифры, '_'\n\n"
        "🌊 **AQUA CHECKER v1.0**",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "back")
async def back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await cmd_start(callback.message)
    await callback.answer()

# ===== ЗАПУСК =====
async def main():
    create_index_html()
    print("🌊 AQUA CHECKER БОТ ЗАПУЩЕН!")
    print(f"📁 Отчёты: {os.path.abspath(REPORTS_DIR)}/")
    print(f"📊 Всего найдено: {len(found_usernames)}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())