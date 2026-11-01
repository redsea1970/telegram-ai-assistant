import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Загружаем переменные из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Токен не найден! Проверьте файл .env")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Простая база знаний (демо)
CATEGORIES = {
    "сварка": "Сварочные аппараты: инверторы, полуавтоматы, аргоновые. Для дома подойдут инверторы до 200А.",
    "компрессор": "Компрессоры: поршневые и винтовые. Для гаража хватит поршневого на 50–100 л.",
    "генератор": "Генераторы: бензиновые и дизельные. Для дачи — бензиновый на 3–5 кВт.",
    "инструмент": "Электроинструмент: дрели, шуруповерты, болгарки. Уточните, для каких задач нужен.",
}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я AI-консультант по оборудованию. 🤖\n"
        "Помогу подобрать инструмент под ваши задачи.\n\n"
        "Напишите, что вы ищете (например: 'сварочный аппарат для дома' или 'компрессор для гаража')."
    )

@dp.message()
async def smart_handler(message: types.Message):
    text = message.text.lower()
    
    found = False
    for key, answer in CATEGORIES.items():
        if key in text:
            await message.answer(f"🔍 Похоже, вам нужно что-то из категории «{key}».\n\n{answer}\n\nУточните бюджет и условия использования, и я дам более точную рекомендацию.")
            found = True
            break
    
    if not found:
        await message.answer(
            f"Вы написали: «{message.text}»\n\n"
            f"Пока я не знаю, что это. Попробуйте спросить про сварку, компрессор, генератор или инструмент."
        )

async def main():
    print("Бот запущен. Нажмите Ctrl+C для остановки.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
