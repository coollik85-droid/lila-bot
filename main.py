import asyncio
import logging
import sys
import gspread
from google.oauth2.service_account import Credentials

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

# Вставьте сюда ваш актуальный токен Telegram-бота
TOKEN = "ВАШ_ТОКЕН_БОТА_ЗДЕСЬ"

# Название вашей Google Таблицы
SPREADSHEET_NAME = "lila_cells_full"

# Настройка доступов к Google Таблицам
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

def get_cell_from_sheet(cell_number: int):
    """Получает данные клетки по её номеру из Google Таблицы"""
    try:
        # Загружаем ключи из локального файла credentials.json
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Открываем таблицу и получаем первый лист
        sheet = client.open(SPREADSHEET_NAME).sheet1  
        data = sheet.get_all_records()
        
        for row in data:
            if int(row.get("number", 0)) == cell_number:
                return {
                    "name": row.get("name"),
                    "level": row.get("level"),
                    "description": row.get("description")
                }
    except Exception as e:
        logging.error(f"Ошибка при чтении Google Таблицы: {e}")
    
    return None


# Инициализация диспетчера и бота
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Приветственное сообщение при старте бота"""
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}!\n"
        "Я бот игры «Лила». Отправь мне номер клетки (от 1 до 72), и я пришлю ее описание из Google Таблицы."
    )

@dp.message(F.text.regexp(r"^\d+$"))
async def cell_number_handler(message: Message) -> None:
    """Обработка ввода номера клетки пользователем"""
    cell_num = int(message.text)
    
    if not (1 <= cell_num <= 72):
        await message.answer("Пожалуйста, введите число от 1 до 72.")
        return

    # Запрашиваем данные из Google Таблицы
    cell_data = get_cell_from_sheet(cell_num)
    
    if cell_data:
        response_text = (
            f"🎯 **Клетка №{cell_num}**\n"
            f"📌 **Название:** {cell_data['name']}\n"
            f"🌐 **Уровень:** {cell_data['level']}\n\n"
            f"📖 **Описание:** {cell_data['description']}"
        )
        await message.answer(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(f"Не удалось найти данные для клетки №{cell_num} в таблице.")

@dp.message()
async def echo_handler(message: Message) -> None:
    """Запасной хэндлер для остальных сообщений"""
    await message.answer("Пожалуйста, отправьте номер клетки от 1 до 72.")


async def main() -> None:
    # Инициализация бота с настройками по умолчанию
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Запуск поллинга
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
