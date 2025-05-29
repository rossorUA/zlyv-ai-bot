from keep_alive import keep_alive
keep_alive()
import os
import time
import random
import json
import requests
from datetime import datetime
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

client = openai.OpenAI(api_key=OPENAI_API_KEY)
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
    news = []
    resp = requests.get("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=30")
    for hit in resp.json().get("hits", []):
        news.append({"title": hit["title"], "url": hit["url"]})
    random.shuffle(news)
    return news

def paraphrase_text(text):
    messages = [
        {"role": "system", "content": "Перепиши цей текст коротко, цікаво та людською мовою, як справжній редактор для Telegram-каналу, без зайвої офіційності та води."},
        {"role": "user", "content": text}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=120,
        temperature=1.1
    )
    return response.choices[0].message.content.strip()

def generate_caption(news, emojis):
    theme = random.choice(STATIC_THEMES)
    emoji = random.choice(emojis)
    intro = f"{emoji} {theme.upper()}"
    text = paraphrase_text(news["title"])
    # Гарантуємо довжину
    if len(text) < MIN_POST_LEN:
        text = paraphrase_text(news["title"]) + " Що скажеш? 🤔"
    return intro + "\n\n" + text + SIGNATURE

def post_news():
    history = load_history()
    news_list = news_list = [{"title": "Супер тестова новина!", "url": "http://test.com"}]
#fetch_fresh_news()
    for news in news_list:
        if news["title"] not in history and news["title"]:
            caption = generate_caption(news, EMOJIS)
            bot.send_message(TELEGRAM_CHANNEL_ID, caption)
            history.add(news["title"])
            save_history(history)
            print("Пост надіслано:", caption[:50])
            break  # Один пост за цикл

#bot.send_message(TELEGRAM_CHANNEL_ID, "🤖 Перевірка: Бот працює?")


if __name__ == "__main__":
    while True:
        now = datetime.now()
        if POSTING_HOURS_START <= now.hour < POSTING_HOURS_END:
            try:
                post_news()
            except Exception as e:
                print(f"Сталася помилка: {e}")
        else:
            print("Зараз не час для постів!")
        time.sleep(600)
