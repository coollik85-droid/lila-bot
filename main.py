import os
import json
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, Update

BOT_TOKEN = "8925097882:AAHvzhCGGV_oXbhkmgzl_-mdy-15hfj_fpM"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

# Загрузка JSON базы
JSON_FILENAME = os.path.join(os.path.dirname(__file__), "lila_cells.json")

def load_lila_data():
    if os.path.exists(JSON_FILENAME):
        with open(JSON_FILENAME, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

LILA_DATA = load_lila_data()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот по игре **Лила**.\n\n"
        "Отправь мне номер клетки (от **1** до **72**), и я покажу её значение.",
        parse_mode="Markdown"
    )

@dp.message(F.text)
async def get_cell_handler(message: Message):
    text = message.text.strip()
    if text in LILA_DATA:
        cell = LILA_DATA[text]
        response = (
            f"📍 **Клетка №{text}**\n"
            f"🏷 **Название:** {cell['name']}\n"
            f"🌀 **Уровень:** {cell['level']}\n\n"
            f"📖 **Значение:** {cell['description']}"
        )
        await message.answer(response, parse_mode="Markdown")
    else:
        if text.isdigit():
            await message.answer("⚠️ В игре Лила всего 72 клетки. Введите число от 1 до 72.")
        else:
            await message.answer("ℹ️ Пожалуйста, просто отправьте число от 1 до 72.")

app = Flask(__name__)

# Создаем постоянный фоновый цикл событий для обработки запросов бота
loop = asyncio.new_event_loop()
import threading
def start_loop(l):
    asyncio.set_event_loop(l)
    l.run_forever()

threading.Thread(target=start_loop, args=(loop,), daemon=True).start()

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_json(force=True)
        update = Update.model_validate(json_data, context={"bot": bot})
        
        # Безопасно отправляем задачу в постоянный фоновый цикл
        asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), loop)
        
        return "OK", 200
    return "Unsupported Media Type", 415

@app.route("/", methods=['GET'])
def index():
    return "Lila Bot is running!", 200
