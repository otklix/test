import random
import string
import os
from datetime import datetime

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_random_username() -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=5))

def create_report(username: str) -> str:
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@{username} — найден!</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        @keyframes wave {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a1a, #1a1a3e, #0a0a1a);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            animation: fadeIn 1s ease-out;
        }}
        
        .container {{
            background: rgba(20, 20, 50, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 30px;
            padding: 40px;
            max-width: 550px;
            width: 100%;
            border: 1px solid rgba(0, 200, 255, 0.1);
            box-shadow: 0 30px 80px rgba(0, 200, 255, 0.1);
            position: relative;
            overflow: hidden;
        }}
        
        .container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 200, 255, 0.08), transparent);
            animation: wave 3s infinite;
        }}
        
        .logo {{
            text-align: center;
            font-size: 28px;
            font-weight: 900;
            color: #00ccff;
            letter-spacing: 3px;
            margin-bottom: 20px;
            position: relative;
            z-index: 1;
        }}
        
        .logo span {{ color: #ffffff; }}
        
        .username {{
            font-size: 48px;
            font-weight: 900;
            color: #00ccff;
            text-align: center;
            margin: 15px 0;
            animation: pulse 2s ease-in-out infinite;
            position: relative;
            z-index: 1;
        }}
        
        .username a {{
            color: #00ccff;
            text-decoration: none;
        }}
        
        .status {{
            display: table;
            margin: 0 auto;
            background: #4CAF50;
            color: white;
            padding: 8px 24px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 14px;
            position: relative;
            z-index: 1;
        }}
        
        .info {{
            color: #6688aa;
            text-align: center;
            margin: 15px 0;
            font-size: 14px;
            position: relative;
            z-index: 1;
        }}
        
        .btn {{
            display: block;
            background: linear-gradient(135deg, #00ccff, #0066ff);
            color: white;
            padding: 16px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 700;
            text-align: center;
            margin-top: 20px;
            transition: all 0.3s;
            position: relative;
            z-index: 1;
        }}
        
        .btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 30px rgba(0, 200, 255, 0.3);
        }}
        
        .footer {{
            text-align: center;
            color: #446688;
            font-size: 11px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(0, 200, 255, 0.05);
            position: relative;
            z-index: 1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">AQUA <span>CHECKER</span></div>
        <div class="username">
            <a href="https://t.me/{username}" target="_blank">@{username}</a>
        </div>
        <div class="status">✅ СВОБОДЕН</div>
        <div class="info">📅 Найден: {now}</div>
        <a href="https://t.me/{username}" target="_blank" class="btn">🚀 Перейти в Telegram</a>
        <div class="footer">AQUA CHECKER • {now}</div>
    </div>
</body>
</html>'''

def create_index():
    reports = os.listdir(REPORTS_DIR)
    list_items = ""
    for r in sorted(reports, reverse=True)[:30]:
        username = r.replace('.html', '')
        list_items += f'<a href="reports/{r}">@{username}</a>\n'
    
    if not list_items:
        list_items = '<p style="color:#6688aa;">Пока нет отчётов</p>'
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AQUA CHECKER</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        @keyframes wave {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
        }}
        
        body {{
            background: linear-gradient(135deg, #0a0a1a, #1a1a3e, #0a0a1a);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            padding: 20px;
            animation: fadeIn 1s ease-out;
        }}
        
        .container {{
            background: rgba(20,20,50,0.95);
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            border: 1px solid rgba(0,200,255,0.1);
            text-align: center;
            position: relative;
            overflow: hidden;
            box-shadow: 0 30px 80px rgba(0,200,255,0.1);
        }}
        
        .container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 200, 255, 0.05), transparent);
            animation: wave 4s infinite;
        }}
        
        .logo {{
            color: #00ccff;
            font-size: 32px;
            font-weight: 900;
            letter-spacing: 3px;
            position: relative;
            z-index: 1;
        }}
        
        .logo span {{ color: #ffffff; }}
        
        .subtitle {{
            color: #6688aa;
            font-size: 14px;
            margin: 10px 0 25px;
            position: relative;
            z-index: 1;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            margin: 25px 0;
            position: relative;
            z-index: 1;
        }}
        
        .stat-box {{
            background: rgba(0,200,255,0.05);
            padding: 15px;
            border-radius: 12px;
            border: 1px solid rgba(0,200,255,0.08);
            transition: all 0.3s;
        }}
        
        .stat-box:hover {{
            transform: scale(1.05);
            background: rgba(0,200,255,0.1);
        }}
        
        .stat-box .number {{
            font-size: 28px;
            font-weight: 800;
            color: #00ccff;
        }}
        
        .stat-box .label {{
            font-size: 11px;
            color: #6688aa;
            text-transform: uppercase;
            margin-top: 3px;
        }}
        
        .recent {{
            position: relative;
            z-index: 1;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(0,200,255,0.05);
        }}
        
        .recent-title {{
            color: #00ccff;
            font-weight: 600;
            margin-bottom: 15px;
        }}
        
        .recent a {{
            color: #00ccff;
            text-decoration: none;
            display: inline-block;
            margin: 5px 8px;
            padding: 6px 16px;
            background: rgba(0,200,255,0.05);
            border-radius: 20px;
            font-size: 14px;
            border: 1px solid rgba(0,200,255,0.05);
            transition: all 0.3s;
        }}
        
        .recent a:hover {{
            background: rgba(0,200,255,0.15);
            transform: scale(1.05);
            border-color: rgba(0,200,255,0.2);
        }}
        
        .footer {{
            color: #446688;
            font-size: 11px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(0,200,255,0.05);
            position: relative;
            z-index: 1;
        }}
        
        .watermark {{
            position: absolute;
            bottom: 10px;
            right: 20px;
            font-size: 60px;
            opacity: 0.05;
            color: #00ccff;
            z-index: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="watermark">🌊</div>
        <div class="logo">AQUA <span>CHECKER</span></div>
        <div class="subtitle">🌊 Найденные юзернеймы</div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="number">{len(reports)}</div>
                <div class="label">Всего</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:#4CAF50;">{len(reports)}</div>
                <div class="label">Валидных</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:#f44336;">0</div>
                <div class="label">Невалидных</div>
            </div>
        </div>
        
        <div class="recent">
            <div class="recent-title">📋 Отчёты:</div>
            {list_items}
        </div>
        
        <div class="footer">Обновлено: {datetime.now().strftime("%d.%m.%Y %H:%M")}</div>
    </div>
</body>
</html>'''

    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    print("🌊 Генерация отчётов...")
    
    # Генерируем 5 случайных юзернеймов
    for _ in range(5):
        username = generate_random_username()
        html = create_report(username)
        
        filepath = os.path.join(REPORTS_DIR, f"{username}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ Создан: {username}.html")
    
    create_index()
    print("✅ index.html создан")
    print("🌊 Готово!")

if __name__ == "__main__":
    main()