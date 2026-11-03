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
    user_id = message.from_user.id
    raw_text = message.text or ""
    masked_text = mask_pii(raw_text)
    text = masked_text.lower()

    remember(user_id, masked_text)

    found = False
    for key, answer in CATEGORIES.items():
        if key in text:
            update_prefs(user_id, key)
            prefs = get_prefs(user_id)
            extra = ""
            if prefs.get("categories") and prefs["categories"][-2:-1] and prefs["categories"][-2] != key:
                extra = f"\n\n(В прошлый раз вы интересовались: {prefs['categories'][-2]}.)"
            reply = f"🔍 Похоже, вам нужно что-то из категории «{key}».\n\n{answer}{extra}\n\nУточните бюджет и условия использования, и я дам более точную рекомендацию."
            await send_with_feedback(message, reply)
            found = True
            break

    if not found:
        reply = (
            f"Вы написали: «{masked_text}»\n\n"
            f"Пока я не знаю, что это. Попробуйте спросить про сварку, компрессор, генератор или инструмент."
        )
        await send_with_feedback(message, reply)

async def main():
    print("Бот запущен. Нажмите Ctrl+C для остановки.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import json
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

FEEDBACK_FILE = "feedback.json"

def load_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        return []
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_feedback(records):
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


async def send_with_feedback(message: types.Message, text: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍", callback_data="fb:up"),
            InlineKeyboardButton(text="👎", callback_data="fb:down"),
        ]
    ])
    await message.answer(text, reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("fb:"))
async def handle_feedback(callback: types.CallbackQuery):
    rating = "up" if callback.data == "fb:up" else "down"
    record = {
        "user_id": callback.from_user.id,
        "username": callback.from_user.username,
        "rating": rating,
        "timestamp": datetime.utcnow().isoformat(),
        "message_id": callback.message.message_id,
    }
    records = load_feedback()
    records.append(record)
    save_feedback(records)
    await callback.answer("Спасибо за отзыв!" if rating == "up" else "Спасибо, учтём!")


# Краткосрочная память: user_id -> список последних сообщений
SHORT_MEMORY = {}
SHORT_MEMORY_LIMIT = 5

PREFS_FILE = "user_prefs.json"

def load_prefs():
    if not os.path.exists(PREFS_FILE):
        return {}
    with open(PREFS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_prefs(prefs):
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)

def update_prefs(user_id, category):
    prefs = load_prefs()
    key = str(user_id)
    user = prefs.get(key, {"categories": [], "short_answers": False})
    if category and category not in user["categories"]:
        user["categories"].append(category)
        user["categories"] = user["categories"][-5:]  # храним последние 5
    prefs[key] = user
    save_prefs(prefs)

def get_prefs(user_id):
    return load_prefs().get(str(user_id), {"categories": [], "short_answers": False})

import re
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\s\-()]{7,}\d)")

def mask_pii(text: str) -> str:
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    return text

def remember(user_id, text):
    SHORT_MEMORY.setdefault(user_id, []).append(text)
    SHORT_MEMORY[user_id] = SHORT_MEMORY[user_id][-SHORT_MEMORY_LIMIT:]

def get_memory(user_id):
    return SHORT_MEMORY.get(user_id, [])

