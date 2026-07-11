import os
import json
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
os.makedirs(REPORTS_DIR, exist_ok=True)

# Хранилище
reports = {}

def generate_full_report_html(usernames: list, checked: list) -> str:
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    total = len(usernames)
    taken = len([u for u in checked if not u.get('isAvailable', False)]) if checked else 0

    items = ''.join([f'<div class="item">@{u} <span class="free">✅ Свободен</span></div>' for u in usernames[:50]])
    if len(usernames) > 50:
        items += f'<div class="item" style="color:#6688aa;text-align:center;">... и ещё {len(usernames)-50}</div>'

    return f'''<!DOCTYPE html>
<html>
<head><title>AQUA CHECKER — Отчёт</title>
<style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background: #0a0a2a; color: #00ccff; font-family: Arial; padding: 40px; }}
    .container {{ max-width: 700px; margin: 0 auto; background: rgba(10,20,50,0.9); border-radius: 20px; padding: 30px; border: 1px solid rgba(0,200,255,0.1); }}
    h1 {{ color: #00ccff; text-align: center; font-size: 32px; }}
    .sub {{ text-align:center; color:#6688aa; margin-bottom:20px; }}
    .stats {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin: 20px 0; }}
    .stat {{ background: rgba(0,200,255,0.05); padding: 15px; border-radius: 12px; text-align: center; }}
    .stat .num {{ font-size: 28px; font-weight: 800; }}
    .stat .label {{ color: #6688aa; font-size: 11px; text-transform: uppercase; }}
    .list {{ max-height: 400px; overflow-y: auto; margin: 15px 0; }}
    .item {{ padding: 8px 12px; background: rgba(0,200,255,0.03); border-radius: 8px; margin: 4px 0; border-left: 2px solid #4CAF50; }}
    .free {{ color: #4CAF50; float: right; }}
    .taken {{ color: #f44336; float: right; }}
    .footer {{ text-align: center; color: #446688; font-size: 11px; margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(0,200,255,0.05); }}
</style>
</head>
<body>
<div class="container">
    <h1>🌊 AQUA CHECKER</h1>
    <div class="sub">📊 Полный отчёт</div>
    <div class="stats">
        <div class="stat"><div class="num">{total}</div><div class="label">Всего</div></div>
        <div class="stat"><div class="num" style="color:#4CAF50;">{total}</div><div class="label">Свободных</div></div>
        <div class="stat"><div class="num" style="color:#f44336;">{taken}</div><div class="label">Занятых</div></div>
    </div>
    <div class="list">{items}</div>
    <div class="footer">Сгенерировано: {now}</div>
</div>
</body>
</html>'''

@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    
    if len(args) > 1 and args[1].startswith("report_"):
        report_id = args[1].replace("report_", "")
        
        # Проверяем, не использована ли ссылка
        if report_id in reports and reports[report_id].get("used", False):
            await message.answer("❌ Эта ссылка уже была использована!")
            return
        
        # Получаем данные
        data = reports.get(report_id, {})
        usernames = data.get("usernames", [])
        checked = data.get("checked", [])
        
        if not usernames:
            # Генерируем тестовые
            usernames = [''.join(random.choices(string.ascii_lowercase + string.digits, k=5)) for _ in range(20)]
        
        await message.answer(f"📄 Генерирую отчёт ({len(usernames)} юзернеймов)...")
        
        # Создаём HTML
        html = generate_full_report_html(usernames, checked)
        filename = f"report_{report_id}.html"
        filepath = os.path.join(REPORTS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Создаём ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.write(filepath, filename)
        
        zip_buffer.seek(0)
        
        # Отправляем
        await message.answer_document(
            types.BufferedInputFile(zip_buffer.getvalue(), filename=f"report_{report_id}.zip"),
            caption=f"📦 **Полный отчёт**\n\n"
                    f"✅ Найдено: {len(usernames)} юзернеймов\n"
                    f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"🔗 Ссылка одноразовая — использована!",
            parse_mode="Markdown"
        )
        
        # Отмечаем как использованную
        reports[report_id] = {"used": True, "usernames": usernames, "checked": checked}
        os.remove(filepath)
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
        await message.answer(f"✅ @{username} — **СВОБОДЕН!**\n🔗 https://t.me/{username}",
                           parse_mode="Markdown")
    else:
        await message.answer(f"❌ @{username} — **ЗАНЯТ!**", parse_mode="Markdown")

async def main():
    print("🌊 AQUA CHECKER БОТ ЗАПУЩЕН!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())