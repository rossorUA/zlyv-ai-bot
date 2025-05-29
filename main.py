from keep_alive import keep_alive
keep_alive()

import os
import time
import random
import json
import datetime
import requests
import openai
from telebot import TeleBot

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
bot = TeleBot(TELEGRAM_BOT_TOKEN)
client = openai.OpenAI()

HISTORY_FILE = "post_history.json"
MAX_POSTS_PER_DAY = 30
POSTING_HOURS_START = 9
POSTING_HOURS_END = 21

MIN_SYMBOLS = 200  # мінімум 200 букв у новині
SIGNATURE = "@zlyv_ai"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False)

def fetch_fresh_news():
    try:
        resp = requests.get("https://ain.ua/feed/")
        if resp.status_code != 200:
            return None
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.content, features="xml")
        items = soup.findAll("item")
        random.shuffle(items)
        for item in items:
            title = item.title.text
            description = item.description.text if item.description else ""
            link = item.link.text
            source_text = f"{title}. {description}\n\n{link}"
            prompt = (
                f"Перепиши цю новину для Telegram-каналу іншими словами українською мовою, "
                f"зберігаючи суть, додай емодзі, справжні абзаци, легку жартівливість. "
                f"Мінімум 200 букв (без пробілів). Не додавай закликів до коментарів або відгуків. "
                f"Підпис обовʼязково — {SIGNATURE} в самому кінці. "
                f"Текст тільки для Telegram, без заголовка. Ось новина:\n\n{source_text}"
            )
            response = client.chat.completions.create(
                model="gpt-4o",  # або gpt-3.5-turbo
                messages=[{"role": "user", "content": prompt}],
                temperature=1,
                max_tokens=320,  # цього більш ніж достатньо
            )
            news = response.choices[0].message.content.strip()
            news = news.rstrip(".")  # прибираємо обрізані крапки
            if not news.endswith(SIGNATURE):
                news = news + "\n\n" + SIGNATURE
            # Рахуємо тільки букви (без пробілів)
            news_symbols = len("".join([c for c in news if c.isalpha()]))
            if news_symbols >= MIN_SYMBOLS:
                return news
        return None
    except Exception as e:
        print(f"❌ OpenAI/News fetch error: {e}")
        return None

def post_to_telegram(text):
    bot.send_message(TELEGRAM_CHANNEL_ID, text)
    print(f"✅ [{datetime.datetime.now().strftime('%H:%M:%S')}] Пост надіслано!")

def random_delay():
    return random.randint(600, 3600)

def main():
    history = load_history()
    post_count = 0
    today = datetime.date.today()

    while True:
        now = datetime.datetime.now()
        if now.date() != today:
            post_count = 0
            today = now.date()

        if not (POSTING_HOURS_START <= now.hour < POSTING_HOURS_END):
            print("🌙 Не робочий час для постингу. Чекаю до ранку...")
            time.sleep(300)
            continue

        if post_count >= MAX_POSTS_PER_DAY:
            print("📅 Досягнуто максимум постів на сьогодні. Чекаю до завтра...")
            time.sleep(3600)
            continue

        post = fetch_fresh_news()
        if not post or post in history:
            print("❗ Не вдалося отримати унікальний новий пост, скипаю цю спробу.")
            time.sleep(300)
            continue

        post_to_telegram(post)
        history.add(post)
        save_history(history)
        post_count += 1

        delay = random_delay()
        print(f"⏳ Наступний пост через {delay // 60} хвилин.")
        time.sleep(delay)

if __name__ == "__main__":
    main()
