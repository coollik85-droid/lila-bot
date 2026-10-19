import os
import json
import asyncio
import threading
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, request
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, Update

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

# Настройки для подключения к Google Таблицам
SPREADSHEET_NAME = "lila_cells_full"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

def get_cell_from_sheet(cell_text: str):
    """Получает данные клетки по её номеру из Google Таблицы"""
    try:
        # Проверяем, задана ли переменная окружения на Render, иначе ищем локальный credentials.json
        google_creds_env = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        
        if google_creds_env:
            creds_dict = json.loads(google_creds_env)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
            
        client = gspread.authorize(creds)
        
        # Открываем таблицу по имени и берем первый лист
        sheet = client.open(SPREADSHEET_NAME).sheet1  
        data = sheet.get_all_records()
        
        for row in data:
            # Ищем строку, где номер клетки совпадает (приводим к строке для надежности)
            if str(row.get("number", "")) == cell_text:
                return {
                    "name": row.get("name"),
                    "level": row.get("level"),
                    "description": row.get("description")
                }
    except Exception as e:
        print(f"Ошибка при чтении Google Таблицы: {e}")
    
    return None

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
    
    # Проверяем, что введено число от 1 до 72
    if text.isdigit() and 1 <= int(text) <= 72:
        cell = get_cell_from_sheet(text)
        if cell:
            response = (
                f"📍 **Клетка №{text}**\n"
                f"🏷 **Название:** {cell['name']}\n"
                f"🌀 **Уровень:** {cell['level']}\n\n"
                f"📖 **Значение:** {cell['description']}"
            )
            await message.answer(response, parse_mode="Markdown")
        else:
            await message.answer("⚠️ Не удалось найти данные для этой клетки в таблице.")
    else:
        if text.isdigit():
            await message.answer("⚠️ В игре Лила всего 72 клетки. Введите число от 1 до 72.")
        else:
            await message.answer("ℹ️ Пожалуйста, просто отправьте число от 1 до 72.")

app = Flask(__name__)

async def process_update(json_data):
    # Экземпляр бота создается внутри асинхронного контекста с закрытием сессии
    async with Bot(token=BOT_TOKEN) as bot_instance:
        update = Update.model_validate(json_data, context={"bot": bot_instance})
        await dp.feed_update(bot=bot_instance, update=update)

def run_async(json_data):
    asyncio.run(process_update(json_data))

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_json(force=True)
        threading.Thread(target=run_async, args=(json_data,)).start()
        return "OK", 200
    return "Unsupported Media Type", 415

@app.route("/", methods=['GET'])
def index():
    return "Lila Bot is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
