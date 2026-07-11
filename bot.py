import os
import asyncio
import json
import random
import string
import zipfile
import io
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "ВАШ_ТОКЕН_БОТА"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# Хранилище одноразовых ссылок
report_links = {}
report_data = {}

# ===== ГЕНЕРАЦИЯ ПОЛНОГО ОТЧЁТА =====
def generate_full_report(usernames: list) -> str:
    """Создаёт красивый HTML-отчёт с метриками"""
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    total = len(usernames)
    valid = total
    invalid = 0
    
    usernames_list = ''.join([f'<div class="username-item">@{u}</div>' for u in usernames[:50]])
    more = f'<div class="username-item" style="color:#6688aa;">... и ещё {total - 50}</div>' if total > 50 else ''
    
    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AQUA CHECKER — Полный отчёт</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        body {{
            background: linear-gradient(135deg, #0a0a1a, #1a1a3e, #0a0a1a);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            padding: 20px;
            animation: fadeIn 0.8s ease-out;
        }}
        
        .container {{
            background: rgba(20, 20, 50, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 30px;
            padding: 40px;
            max-width: 700px;
            width: 100%;
            border: 1px solid rgba(0, 200, 255, 0.1);
            box-shadow: 0 30px 80px rgba(0, 200, 255, 0.1);
        }}
        
        .logo {{
            text-align: center;
            font-size: 28px;
            font-weight: 900;
            color: #00ccff;
            letter-spacing: 3px;
        }}
        
        .logo span {{ color: #ffffff; }}
        
        .header {{
            text-align: center;
            border-bottom: 1px solid rgba(0, 200, 255, 0.05);
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }}
        
        .stat-box {{
            background: rgba(0, 200, 255, 0.03);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid rgba(0, 200, 255, 0.05);
        }}
        
        .stat-box .number {{
            font-size: 28px;
            font-weight: 800;
            color: #00ccff;
        }}
        
        .stat-box .number.green {{ color: #4CAF50; }}
        .stat-box .number.red {{ color: #f44336; }}
        .stat-box .label {{
            font-size: 11px;
            color: #6688aa;
            text-transform: uppercase;
            margin-top: 5px;
        }}
        
        .username-list {{
            max-height: 400px;
            overflow-y: auto;
            margin: 15px 0;
            padding-right: 5px;
        }}
        
        .username-list::-webkit-scrollbar {{
            width: 4px;
        }}
        
        .username-list::-webkit-scrollbar-track {{
            background: rgba(0, 200, 255, 0.05);
            border-radius: 10px;
        }}
        
        .username-list::-webkit-scrollbar-thumb {{
            background: #00ccff;
            border-radius: 10px;
        }}
        
        .username-item {{
            background: rgba(0, 200, 255, 0.03);
            padding: 8px 12px;
            border-radius: 8px;
            margin: 4px 0;
            color: #00ccff;
            font-size: 14px;
            font-weight: 500;
            border-left: 2px solid #4CAF50;
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
            <div style="color:#6688aa;font-size:14px;margin-top:5px;">📊 Полный отчёт</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-box">
                <div class="number">{total}</div>
                <div class="label">Всего</div>
            </div>
            <div class="stat-box">
                <div class="number green">{valid}</div>
                <div class="label">Валидных</div>
            </div>
            <div class="stat-box">
                <div class="number red">{invalid}</div>
                <div class="label">Невалидных</div>
            </div>
            <div class="stat-box">
                <div class="number">0</div>
                <div class="label">Забаненных</div>
            </div>
        </div>
        
        <div style="color:#6688aa;font-size:13px;margin-bottom:10px;">📋 Найденные юзернеймы:</div>
        <div class="username-list">
            {usernames_list}
            {more}
        </div>
        
        <div class="footer">Сгенерировано: {now}</div>
    </div>
</body>
</html>'''

# ===== БОТ =====
@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    
    if len(args) > 1:
        param = args[1]
        
        if param.startswith("report_"):
            report_id = param.replace("report_", "")
            
            # Проверяем, существует ли отчёт
            if report_id in report_data:
                data = report_data[report_id]
                
                # Проверяем, не использована ли ссылка (одноразовая)
                if report_links.get(report_id, {}).get("used", False):
                    await message.answer("❌ Эта ссылка уже была использована!")
                    return
                
                # Отмечаем как использованную
                report_links[report_id] = {"used": True, "user_id": message.from_user.id}
                
                # Генерируем отчёт
                await message.answer("📄 Генерирую полный отчёт...")
                
                usernames = data.get("usernames", [])
                html = generate_full_report(usernames)
                
                # Сохраняем HTML
                filename = f"report_{report_id}.html"
                filepath = os.path.join(REPORTS_DIR, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html)
                
                # Создаём ZIP
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    zip_file.write(filepath, filename)
                
                zip_buffer.seek(0)
                
                # Отправляем файл
                await message.answer_document(
                    types.BufferedInputFile(zip_buffer.getvalue(), filename=f"report_{report_id}.zip"),
                    caption=f"📦 **Полный отчёт**\n\n"
                            f"✅ Найдено: {len(usernames)} юзернеймов\n"
                            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                            f"🔗 Ссылка одноразовая — использована!",
                    parse_mode="Markdown"
                )
                
                # Удаляем файлы
                os.remove(filepath)
                del report_data[report_id]
                del report_links[report_id]
                
                return
    
    # Обычный старт
    await message.answer(
        "🌊 **AQUA CHECKER**\n\n"
        "🔍 Напиши юзернейм для проверки\n"
        "📄 Используй сайт для массового поиска",
        parse_mode="Markdown"
    )

@dp.message()
async def check(message: types.Message):
    username = message.text.strip().lower().replace('@', '')
    
    if len(username) < 5:
        await message.answer("❌ Минимум 5 символов!")
        return
    
    # Проверка через API
    import aiohttp
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/checkUsername"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"username": username}) as response:
            data = await response.json()
            is_available = data.get("result", False)
    
    if is_available:
        await message.answer(f"✅ @{username} — **СВОБОДЕН!**\n🔗 https://t.me/{username}",
                           parse_mode="Markdown")
    else:
        await message.answer(f"❌ @{username} — **ЗАНЯТ!**", parse_mode="Markdown")

# ===== API ДЛЯ САЙТА =====
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

@app.route("/api/create_report", methods=["POST"])
def create_report():
    data = request.json
    usernames = data.get("usernames", [])
    
    if not usernames:
        return jsonify({"error": "Нет юзернеймов"}), 400
    
    # Генерируем ID отчёта
    report_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + ''.join(random.choices(string.ascii_lowercase, k=6))
    
    # Сохраняем данные
    report_data[report_id] = {"usernames": usernames}
    report_links[report_id] = {"used": False}
    
    # Ссылка для бота
    bot_link = f"https://t.me/Username1FinderBOT?start=report_{report_id}"
    
    return jsonify({
        "report_id": report_id,
        "bot_link": bot_link,
        "count": len(usernames)
    })

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# ===== ЗАПУСК =====
async def main():
    # Запускаем Flask в отдельном потоке
    thread = threading.Thread(target=run_flask, daemon=True)
    thread.start()
    
    print("🌊 AQUA CHECKER БОТ ЗАПУЩЕН!")
    print("📁 Отчёты:", os.path.abspath(REPORTS_DIR))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())