
import os
import time
import random
import json
from datetime import datetime
import requests
from keep_alive import keep_alive

import telebot
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
bot = telebot.TeleBot(TOKEN)

POSTS = [
    "Textual — новий фреймворк на Python для створення TUI-додатків у терміналі з логікою як у фронтенду.\n\nВін дає змогу створювати компоненти інтерфейсу як у React, але прямо в CLI.",
    "Google DeepMind представив RT-2.5 — мультимодальну модель, яка інтерпретує відео як серіальні епізоди, розуміючи не просто кадри, а цілісні сцени та мотивацію.",
    "GPT-4o тепер перебиває тебе вголос. OpenAI тестує нову голосову модель, яка не просто говорить, а здатна розпізнати, коли користувач починає говорити — й перебити його.\n\nЦе дозволяє ШІ реагувати як реальний співрозмовник з емоціями та плавністю.",
    "Meta показала ШІ, який читає думки з EEG-даних. Модель здатна реконструювати прості образи на основі мозкової активності.\n\nЦе ще не телепатія, але дуже близько.",
    "Python отримав нову бібліотеку Pydantic v2 — тепер вона у 12 разів швидша і повністю переписана на Rust.\n\nВалідація даних стала ще простішою та ефективнішою.",
]

HISTORY_FILE = "history.json"
used_posts = []

if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        used_posts = json.load(f)

def save_history():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(used_posts, f)

def choose_post():
    available = [p for p in POSTS if p not in used_posts]
    if not available:
        used_posts.clear()
        save_history()
        available = POSTS
    post = random.choice(available)
    used_posts.append(post)
    save_history()
    return post

def post_news():
    post = choose_post()
    text = f"{post}\n\n@zlyv_ai"
    bot.send_message(CHANNEL_ID, text)

keep_alive()
bot.send_message(CHANNEL_ID, "⚡ Старт автозливу. Далі — кожні 10 хв.\n@zlyv_ai")

while True:
    try:
        post_news()
    except Exception as e:
        print(f"Error sending post: {e}")
    time.sleep(600)  # 10 хв
