from keep_alive import keep_alive
keep_alive()
import os
import time
import random
import json
import requests
from datetime import datetime, timedelta
import openai
from telebot import TeleBot

# --- Конфіг ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

MAX_POSTS_PER_DAY = 30
POSTING_HOURS_START = 9
POSTING_HOURS_END = 21
MIN_POST_LEN = 200
MAX_POST_LEN = 250

HISTORY_FILE = "post_history.json"
EMOJIS = ['🔥', '🤖', '🦾', '🚀', '🧠', '✨', '💡', '😎', '🎉', '🌟', '📱', '🛠', '👾']
SIGNATURE = "\n@zlyv_ai"

STATIC_THEMES = [
    "AI-новинки", "фреймворки", "інсайди", "нові інструменти", "Google", "GitHub", "лайфхаки", 
    "open-source", "ProductHunt", "Bun", "Deno", "Next.js", "Qwik", "Astro", "VS Code", 
    "Copilot", "аналітика", "тренди"
]

openai.api_key = OPENAI_API_KEY
bot = TeleBot(TELEGRAM_BOT_TOKEN)


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False)

def fetch_fresh_news():
    # Можеш замінити парсер на свій, зараз для прикладу — Habr (API нема, беремо random з open-source).
    # Тут має бути твій парсер новин — НЕ ЗАЛИШАЙ просто як є, бо буде дублювати старе!
    news = []
    resp = requests.get("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=30")
    for hit in resp.json().get("hits", []):
        news.append({"title": hit["title"], "url": hit["url"]})
    random.shuffle(news)
    return news

def paraphrase_text(text):
    # Перефразувати через OpenAI (gpt-3.5-turbo)
    messages = [
        {"role": "system", "content": "Перепиши цей текст коротко, цікаво та людською мовою, як справжній редактор для Telegram-каналу, без зайвої офіційності та води."},
        {"role": "user", "content": text}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=120,
        temperature=1.1
    )
    return response["choices"][0]["message"]["content"]

def generate_caption(news, emojis):
    theme = random.choice(STATIC_THEMES)
    emoji = random.choice(emojis)
    intro = f"{emoji} {theme.upper()}"
    text = paraphrase_text(news["title"])

    # Гарантуємо довжину
    if len(text) < MIN_POST_LEN:
        text = paraphrase_text(news["title"]) + " Що скажеш? 🤔"

    return intro + "\n\n" + text


