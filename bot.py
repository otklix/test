import os
import asyncio
import aiohttp
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask, request, jsonify
import threading

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "ВАШ_ТОКЕН_БОТА"
WEBHOOK_URL = "https://ваш-username.github.io/ваш-репозиторий/webhook"  # Замените!

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = Flask(__name__)

# ===== ОБРАБОТЧИКИ =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("✅ Бот работает через вебхук!")

@dp.message()
async def echo(message: types.Message):
    username = message.text.strip().lower().replace('@', '')
    if len(username) >= 5:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/checkUsername"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"username": username}) as response:
                data = await response.json()
                is_available = data.get("result", False)
        if is_available:
            await message.answer(f"✅ @{username} — СВОБОДЕН!")
        else:
            await message.answer(f"❌ @{username} — ЗАНЯТ!")
    else:
        await message.answer("❌ Минимум 5 символов!")

# ===== ВЕБХУК =====
@app.route("/webhook", methods=["POST"])
async def webhook():
    update_data = request.get_json()
    update = types.Update(**update_data)
    await dp.process_update(update)
    return "OK", 200

@app.route("/")
def index():
    return "🤖 Бот работает!"

# ===== НАСТРОЙКА ВЕБХУКА =====
def set_webhook():
    import requests
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    response = requests.post(url, json={"url": WEBHOOK_URL})
    print("Webhook настроен:", response.json())

# ===== ЗАПУСК =====
def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    # Настройка вебхука
    set_webhook()
    
    # Запуск Flask
    run_flask()