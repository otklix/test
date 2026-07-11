import os
import asyncio
import random
import string
import aiohttp
import json
import base64
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import io
import subprocess

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "ВАШ_ТОКЕН_БОТА"

# Для GitHub Pages
GITHUB_REPO = os.environ.get("GITHUB_REPO", "ваш-username/ваш-репозиторий")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # Токен для пуша в репозиторий
GITHUB_PAGES_URL = os.environ.get("GITHUB_PAGES_URL", "https://ваш-username.github.io/ваш-репозиторий")

REPORTS_DIR = "reports"
IMAGES_DIR = "images"
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

MAX_ATTEMPTS = 50
TIMEOUT = 0.3

# ===== ИНИЦИАЛИЗАЦИЯ БОТА =====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

class SearchStates(StatesGroup):
    waiting_for_username = State()

# ===== СОЗДАНИЕ ПРОГРЕСС-БАРА (GIF/PNG) =====
def create_progress_image(progress: int, total: int, username: str = "", status: str = "Поиск") -> bytes:
    """Создаёт стильный прогресс-бар с плавным дизайном"""
    width, height = 800, 300
    percent = (progress / total) * 100 if total > 0 else 0
    
    img = Image.new('RGB', (width, height), color=(15, 15, 35))
    draw = ImageDraw.Draw(img)
    
    # Градиентный фон
    for i in range(height):
        r = 15 + int(i * 0.05)
        g = 15 + int(i * 0.03)
        b = 35 + int(i * 0.1)
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 32)
        font_progress = ImageFont.truetype("arial.ttf", 24)
        font_username = ImageFont.truetype("arial.ttf", 20)
        font_status = ImageFont.truetype("arial.ttf", 18)
    except:
        font_title = ImageFont.load_default()
        font_progress = ImageFont.load_default()
        font_username = ImageFont.load_default()
        font_status = ImageFont.load_default()
    
    # Заголовок
    draw.text((width//2 - 100, 20), "🔍 ПОИСК ЮЗЕРНЕЙМА", fill=(255, 255, 255), font=font_title)
    
    # Рамка прогресс-бара
    bar_x, bar_y, bar_w, bar_h = 50, 90, width - 100, 50
    draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], 
                   outline=(100, 100, 200), width=2, fill=(30, 30, 70))
    
    # Заливка прогресса (градиент)
    fill_width = int((bar_w - 4) * (percent / 100))
    if fill_width > 0:
        for i in range(fill_width):
            ratio = i / fill_width
            r = int(0 + ratio * 100)
            g = int(100 + ratio * 100)
            b = int(200 + ratio * 55)
            draw.line([(bar_x + 2 + i, bar_y + 2), (bar_x + 2 + i, bar_y + bar_h - 2)], 
                     fill=(r, g, b), width=1)
    
    # Текст прогресса
    progress_text = f"{progress} / {total}  |  {percent:.1f}%"
    draw.text((width//2 - 80, 155), progress_text, fill=(200, 220, 255), font=font_progress)
    
    # Имя юзернейма
    if username:
        draw.text((50, 205), f"🎯 Юзернейм: @{username}", fill=(100, 255, 150), font=font_username)
    
    # Статус
    status_colors = {"Поиск": (100, 200, 255), "Найден": (100, 255, 150), "Занят": (255, 150, 150), "Ошибка": (255, 100, 100)}
    color = status_colors.get(status, (200, 200, 200))
    draw.text((width - 200, 205), f"📌 {status}", fill=color, font=font_status)
    
    img_path = os.path.join(IMAGES_DIR, f"progress_{progress}_{datetime.now().timestamp()}.png")
    img.save(img_path)
    
    with open(img_path, 'rb') as f:
        image_data = f.read()
    
    os.remove(img_path)
    return image_data

# ===== СОЗДАНИЕ HTML-ОТЧЁТА ДЛЯ GITHUB PAGES =====
def create_report_html(username: str, status: str = "Свободен") -> str:
    """Создаёт красивый HTML-отчёт для GitHub Pages"""
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    telegram_link = f"https://t.me/{username}"
    report_id = f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@{username} — найден!</title>
    <meta property="og:title" content="@{username} — свободный юзернейм!">
    <meta property="og:description" content="Найден свободный юзернейм @{username} в Telegram">
    <meta property="og:image" content="https://img.icons8.com/fluency/96/telegram-app.png">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        @keyframes gradient {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
            50% {{ transform: translateY(-10px) rotate(5deg); }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.05); opacity: 0.8; }}
        }}
        
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(50px) scale(0.9); }}
            to {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        
        @keyframes shine {{
            0% {{ left: -100%; }}
            100% {{ left: 200%; }}
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            animation: gradient 15s ease infinite;
            background-size: 400% 400%;
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 30px;
            padding: 50px 40px;
            max-width: 550px;
            width: 100%;
            box-shadow: 0 30px 80px rgba(0,0,0,0.4);
            animation: slideIn 0.8s ease-out;
            position: relative;
            overflow: hidden;
        }}
        
        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 50%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shine 3s infinite;
            pointer-events: none;
        }}
        
        .card::after {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: conic-gradient(from 0deg, transparent, rgba(102, 126, 234, 0.05), transparent, rgba(118, 75, 162, 0.05), transparent);
            animation: spin 20s linear infinite;
            pointer-events: none;
        }}
        
        @keyframes spin {{
            100% {{ transform: rotate(360deg); }}
        }}
        
        .emoji-big {{
            font-size: 80px;
            animation: float 2s ease-in-out infinite;
            position: relative;
            z-index: 1;
            display: block;
            text-align: center;
        }}
        
        .title {{
            font-size: 26px;
            font-weight: 800;
            color: #333;
            margin: 15px 0 5px;
            position: relative;
            z-index: 1;
            text-align: center;
        }}
        
        .username-display {{
            font-size: 48px;
            font-weight: 900;
            color: #667eea;
            margin: 15px 0;
            word-break: break-all;
            position: relative;
            z-index: 1;
            animation: pulse 2s ease-in-out infinite;
            text-align: center;
        }}
        
        .username-display a {{
            color: #667eea;
            text-decoration: none;
            transition: all 0.3s;
        }}
        
        .username-display a:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}
        
        .badge {{
            display: inline-block;
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            padding: 8px 28px;
            border-radius: 50px;
            font-size: 16px;
            font-weight: 700;
            position: relative;
            z-index: 1;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
            text-align: center;
            margin: 0 auto;
            display: table;
        }}
        
        .badge::after {{
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(135deg, #4CAF50, #45a049, #4CAF50);
            border-radius: 50px;
            z-index: -1;
            filter: blur(8px);
            opacity: 0.6;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin: 25px 0;
            position: relative;
            z-index: 1;
        }}
        
        .info-item {{
            background: rgba(102, 126, 234, 0.08);
            padding: 12px 15px;
            border-radius: 12px;
            border: 1px solid rgba(102, 126, 234, 0.1);
        }}
        
        .info-item .label {{
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}
        
        .info-item .value {{
            font-size: 16px;
            color: #333;
            font-weight: 600;
            margin-top: 3px;
            word-break: break-all;
        }}
        
        .btn {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 16px 40px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 700;
            font-size: 18px;
            margin: 15px 0 5px;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
            position: relative;
            z-index: 1;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            width: 100%;
            text-align: center;
        }}
        
        .btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(102, 126, 234, 0.5);
        }}
        
        .footer {{
            margin-top: 20px;
            color: #999;
            font-size: 12px;
            text-align: center;
            position: relative;
            z-index: 1;
            border-top: 1px solid #eee;
            padding-top: 20px;
        }}
        
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        .report-id {{
            font-size: 11px;
            color: #bbb;
            margin-top: 5px;
        }}
        
        @media (max-width: 480px) {{
            .card {{ padding: 30px 20px; }}
            .username-display {{ font-size: 36px; }}
            .title {{ font-size: 22px; }}
            .info-grid {{ grid-template-columns: 1fr; }}
            .btn {{ font-size: 16px; padding: 14px 30px; }}
        }}
    </style>
</head>
<body>
    <div class="card">
        <span class="emoji-big">🎉</span>
        <h1 class="title">Юзернейм найден!</h1>
        
        <div class="username-display">
            <a href="{telegram_link}" target="_blank">@{username}</a>
        </div>
        
        <div class="badge">✅ {status}</div>
        
        <div class="info-grid">
            <div class="info-item">
                <div class="label">📅 Дата</div>
                <div class="value">{now}</div>
            </div>
            <div class="info-item">
                <div class="label">🔗 Ссылка</div>
                <div class="value"><a href="{telegram_link}" target="_blank" style="color:#667eea;text-decoration:none;">t.me/{username}</a></div>
            </div>
            <div class="info-item">
                <div class="label">📊 Статус</div>
                <div class="value" style="color:#4CAF50;">Доступен</div>
            </div>
            <div class="info-item">
                <div class="label">🆔 ID отчёта</div>
                <div class="value" style="font-size:12px;">{report_id}</div>
            </div>
        </div>
        
        <a href="{telegram_link}" target="_blank" class="btn">🚀 Перейти в Telegram</a>
        
        <div class="footer">
            <div>Отчёт сгенерирован автоматически</div>
            <div class="report-id">ID: {report_id}</div>
            <div style="margin-top:5px;">
                <a href="{GITHUB_PAGES_URL}">🏠 На главную</a>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    return html

# ===== СОЗДАНИЕ index.html ДЛЯ GITHUB PAGES =====
def create_index_html():
    """Создаёт красивую главную страницу для GitHub Pages"""
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Юзернейм Бот — Найди свой идеальный ник!</title>
    <meta property="og:title" content="Юзернейм Бот — Найди свободный ник в Telegram">
    <meta property="og:description" content="Поиск 5-символьных юзернеймов в Telegram с красивыми отчётами">
    <meta property="og:image" content="https://img.icons8.com/fluency/96/telegram-app.png">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        @keyframes gradient {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-20px); }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.1); opacity: 0.8; }}
        }}
        
        @keyframes slideUp {{
            from {{ opacity: 0; transform: translateY(50px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            animation: gradient 15s ease infinite;
            background-size: 400% 400%;
        }}
        
        .container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 30px;
            padding: 50px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 30px 80px rgba(0,0,0,0.4);
            animation: slideUp 0.8s ease-out;
            text-align: center;
        }}
        
        .logo {{
            font-size: 80px;
            animation: float 3s ease-in-out infinite;
        }}
        
        h1 {{
            font-size: 36px;
            font-weight: 800;
            color: #333;
            margin: 20px 0 10px;
        }}
        
        .subtitle {{
            color: #666;
            font-size: 18px;
            margin-bottom: 30px;
        }}
        
        .features {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 30px 0;
        }}
        
        .feature {{
            background: rgba(102, 126, 234, 0.08);
            padding: 15px;
            border-radius: 15px;
            border: 1px solid rgba(102, 126, 234, 0.1);
            transition: all 0.3s;
        }}
        
        .feature:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
        }}
        
        .feature .icon {{ font-size: 30px; }}
        .feature .label {{ font-weight: 600; color: #333; margin-top: 5px; }}
        .feature .desc {{ font-size: 12px; color: #888; margin-top: 3px; }}
        
        .btn {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 16px 40px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 700;
            font-size: 18px;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }}
        
        .btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(102, 126, 234, 0.5);
        }}
        
        .stats {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            display: flex;
            justify-content: space-around;
        }}
        
        .stat-item .number {{
            font-size: 24px;
            font-weight: 800;
            color: #667eea;
        }}
        .stat-item .label {{
            font-size: 12px;
            color: #888;
        }}
        
        .recent {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        
        .recent a {{
            color: #667eea;
            text-decoration: none;
            display: inline-block;
            margin: 5px 10px;
            padding: 5px 15px;
            background: rgba(102, 126, 234, 0.08);
            border-radius: 20px;
            font-size: 14px;
            transition: all 0.3s;
        }}
        
        .recent a:hover {{
            background: rgba(102, 126, 234, 0.2);
            transform: scale(1.05);
        }}
        
        @media (max-width: 480px) {{
            .container {{ padding: 30px 20px; }}
            .features {{ grid-template-columns: 1fr; }}
            h1 {{ font-size: 28px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🤖</div>
        <h1>Юзернейм Бот</h1>
        <div class="subtitle">Находи свободные 5-символьные юзернеймы в Telegram</div>
        
        <div class="features">
            <div class="feature">
                <div class="icon">🔍</div>
                <div class="label">Быстрый поиск</div>
                <div class="desc">Проверка через API</div>
            </div>
            <div class="feature">
                <div class="icon">📊</div>
                <div class="label">Прогресс-бар</div>
                <div class="desc">Визуальный процесс</div>
            </div>
            <div class="feature">
                <div class="icon">📄</div>
                <div class="label">Индивидуальные отчёты</div>
                <div class="desc">Каждый юзернейм уникален</div>
            </div>
            <div class="feature">
                <div class="icon">✨</div>
                <div class="label">Красивый дизайн</div>
                <div class="desc">Анимации и градиенты</div>
            </div>
        </div>
        
        <a href="https://t.me/ваш_бот" target="_blank" class="btn">🚀 Запустить бота</a>
        
        <div class="stats">
            <div class="stat-item">
                <div class="number">⚡</div>
                <div class="label">Мгновенный</div>
            </div>
            <div class="stat-item">
                <div class="number">🔒</div>
                <div class="label">Безопасный</div>
            </div>
            <div class="stat-item">
                <div class="number">📱</div>
                <div class="label">Доступный</div>
            </div>
        </div>
        
        <div class="recent">
            <div style="font-weight:600;color:#333;margin-bottom:10px;">📋 Последние найденные:</div>
            <div id="recent-list">
                <!-- Обновляется автоматически через GitHub Pages -->
                <span style="color:#888;">Загрузка...</span>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(html)
    return "index.html"

# ===== ПУШ В GITHUB =====
def push_to_github(file_path: str, message: str = "Update report"):
    """Пушит файл в GitHub репозиторий"""
    if not GITHUB_TOKEN:
        print("⚠️ Нет GITHUB_TOKEN, файл сохранён локально")
        return False
    
    try:
        # Читаем файл
        with open(file_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        
        # Определяем путь в репозитории
        if file_path.startswith("reports/"):
            path = file_path
        else:
            path = file_path
        
        # API запрос к GitHub
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
        
        # Пытаемся получить существующий файл (для обновления)
        import requests
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Проверяем, существует ли файл
        response = requests.get(url, headers=headers)
        sha = None
        if response.status_code == 200:
            sha = response.json().get("sha")
        
        # Создаём/обновляем файл
        data = {
            "message": message,
            "content": content,
            "branch": "main"
        }
        if sha:
            data["sha"] = sha
        
        response = requests.put(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            print(f"✅ Файл {path} запушен в GitHub")
            return True
        else:
            print(f"❌ Ошибка пуша: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

# ===== ОСНОВНЫЕ ОБРАБОТЧИКИ =====
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 **Привет! Я помогу найти свободный юзернейм!**\n\n"
        "🔍 **Как я работаю:**\n"
        "• Напиши мне юзернейм (например, `abcdx`)\n"
        "• Я проверю, свободен ли он\n"
        "• Если занят — найду похожие варианты\n"
        "• Найденные сохраню в красивый отчёт на GitHub Pages\n\n"
        f"📄 Отчёты публикуются здесь: {GITHUB_PAGES_URL}\n\n"
        "✨ **Попробуй прямо сейчас!**",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Начать поиск", callback_data="start_search")],
            [InlineKeyboardButton(text="📋 Все находки", callback_data="my_found")],
            [InlineKeyboardButton(text="🌐 GitHub Pages", url=GITHUB_PAGES_URL)],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
        ])
    )

@router.callback_query(F.data == "start_search")
async def start_search(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "✏️ **Напиши юзернейм для поиска:**\n\n"
        "• Просто юзернейм: `abcdx`\n"
        "• С маской: `a****` (начинается на 'a')\n"
        "• Без @ и пробелов\n\n"
        "⏳ Минимум 5 символов!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
        ])
    )
    await state.set_state(SearchStates.waiting_for_username)
    await callback.answer()

@router.message(SearchStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext, bot: Bot):
    username = message.text.strip().lower().replace('@', '').strip()
    
    if len(username) < 5:
        await message.answer("❌ Юзернейм должен быть минимум **5 символов**!", parse_mode="Markdown")
        return
    
    if not all(c.isalnum() or c == '_' or c == '*' for c in username):
        await message.answer("❌ Только латиница, цифры, '_' и '*' !")
        return
    
    await message.answer(f"🔍 Ищу **@{username}**...", parse_mode="Markdown")
    
    is_available = await check_username(username, bot)
    
    if is_available:
        await generate_report(username, message)
    else:
        await message.answer(f"❌ **@{username}** занят!\n\n🔍 Ищу похожие варианты...", parse_mode="Markdown")
        await search_similar(username, message, bot)
    
    await state.clear()

async def check_username(username: str, bot: Bot) -> bool:
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

async def search_similar(pattern: str, message: Message, bot: Bot):
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
        
        is_available = await check_username(new_username, bot)
        
        if is_available:
            await status_msg.delete()
            await message.answer(f"🎉 **Нашёл!** @{new_username} — СВОБОДЕН!", parse_mode="Markdown")
            await generate_report(new_username, message)
            found = True
            break
        
        await asyncio.sleep(TIMEOUT)
    
    if not found:
        await status_msg.delete()
        await message.answer("😔 Не удалось найти свободный юзернейм. Попробуйте другую маску!")

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
    """Генерирует отчёт и пушит в GitHub Pages"""
    # Создаём HTML
    html_content = create_report_html(username, "Свободен")
    
    # Сохраняем локально
    filepath = os.path.join(REPORTS_DIR, f"{username}.html")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Пушим в GitHub
    pushed = push_to_github(filepath, f"Найден юзернейм @{username}")
    
    # Ссылка на отчёт
    report_url = f"{GITHUB_PAGES_URL}/reports/{username}.html"
    
    # Создаём прогресс-бар "Найден!"
    found_img = create_progress_image(100, 100, username, "Найден")
    photo = BufferedInputFile(found_img, filename="found.png")
    
    await message.answer_photo(
        photo,
        caption=f"🎉 **Юзернейм найден!**\n\n"
                f"📌 **@{username}** — СВОБОДЕН!\n"
                f"🔗 Ссылка: https://t.me/{username}\n"
                f"📄 Отчёт: {report_url}\n\n"
                f"{'✅ Опубликован на GitHub Pages!' if pushed else '📁 Сохранён локально!'}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 Открыть отчёт", url=report_url)],
            [InlineKeyboardButton(text="🚀 Перейти в Telegram", url=f"https://t.me/{username}")],
            [InlineKeyboardButton(text="🔍 Искать ещё", callback_data="start_search")]
        ])
    )

@router.callback_query(F.data == "my_found")
async def my_found(callback: CallbackQuery):
    reports = os.listdir(REPORTS_DIR)
    if not reports:
        await callback.message.answer("📭 Пока нет найденных юзернеймов!")
        await callback.answer()
        return
    
    text = "📋 **Найденные юзернеймы:**\n\n"
    for report in reports[-20:]:
        username = report.replace('.html', '')
        text += f"• @{username} — [Открыть]({GITHUB_PAGES_URL}/reports/{report})\n"
    
    text += f"\n🌐 Все отчёты: {GITHUB_PAGES_URL}"
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "help")
async def help_cmd(callback: CallbackQuery):
    await callback.message.answer(
        "📚 **Помощь:**\n\n"
        "🔹 **Команды:**\n"
        "/start — Главное меню\n"
        "Напиши юзернейм — начать поиск\n\n"
        "🔹 **Маска:**\n"
        "`a****` — найдет все на 'a'\n"
        "`ab***` — начинается на 'ab'\n\n"
        "🔹 **Ограничения:**\n"
        "• 5+ символов\n"
        "• Только латиница, цифры, '_'\n\n"
        f"🌐 Все отчёты: {GITHUB_PAGES_URL}\n\n"
        "Удачи! 🍀",
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
    # Создаём index.html
    create_index_html()
    print("✅ index.html создан")
    
    # Создаём reports папку с .gitkeep
    Path(REPORTS_DIR, ".gitkeep").touch(exist_ok=True)
    
    print("🤖 Бот запущен!")
    print(f"🌐 GitHub Pages: {GITHUB_PAGES_URL}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())