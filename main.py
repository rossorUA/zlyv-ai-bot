import os
import time
import random
import json
import openai
import requests
from telebot import TeleBot

# ======================
# 1. Конфігурація
# ======================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HISTORY_FILE = "post_history.json"

bot = TeleBot(TELEGRAM_BOT_TOKEN)
openai.api_key = OPENAI_API_KEY

THEMES = [
    "Нові AI-інструменти для програмістів",
    "Трендові фреймворки JavaScript",
    "Лайфхаки з Python",
    "Технологічні інсайди від Google",
    "Меми та прикольні утиліти для розробки",
    "Свіжі релізи Node.js, VS Code, TypeScript",
    "Цікаві open-source проекти",
    "AI-рішення для автоматизації роботи",
    "Тренди розробки в 2025",
    "Все, що бентежить сучасного розробника"
    # Додавай свої теми!
]

EMOJIS = ["🔥", "🤖", "💡", "✨", "🚀", "🧠", "⚡", "📢", "🌟", "🦾", "💻"]

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False)

def generate_post():
    theme = random.choice(THEMES)
    prompt = (
        f"Напиши унікальну, цікаву авторську новину українською мовою для Telegram-каналу про IT/AI та програмування. "
        f"Тема: {theme}. Обовʼязково пиши не менше 350 символів, структуровано по абзацах, додавай живі думки, корисні поради, свіжі інсайди, прикольний авторський стиль. "
        f"Використовуй багато emoji на кшталт {' '.join(EMOJIS)} для яскравого вигляду! Завжди завершуй підписом: @zlyv_ai. "
        f"Пост має бути абсолютно новим, унікальним, ніде не використаним раніше. Додай, будь ласка, не менше трьох реальних абзаців (кожен на новий рядок)."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # або "gpt-3.5-turbo" якщо немає доступу до gpt-4
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=1
    )
    return response.choices[0].message["content"].strip()

def generate_image(post_text):
    prompt = (
        f"Згенеруй унікальну ілюстрацію для Telegram-поста на тему: \"{post_text[:100]}...\" "
        f"у стилі сучасного digital-art для IT/AI-каналу. Без тексту."
    )
    dalle_response = openai.Image.create(
        prompt=prompt,
        n=1,
        si
