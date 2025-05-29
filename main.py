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

EMOJIS = [
    "🔥", "🚀", "💡", "🤖", "🧠", "🌟", "⚡️", "✨", "🎯", "🦾", "💥", "🧩", "📣", "📝", "😎",
    "🥳", "👾", "🕹️", "💻", "🧑‍💻", "👨‍💻", "👩‍💻", "🎉"
]
PIKA_JOKES = [
    "Реально кайфую з цієї новини! 😎",
    "Ну тут навіть ШІ офігів би 🤖",
    "Така новина, що навіть робот задумався... 🦾",
    "Інфа, яка заслуговує на зберегти в закладки! ⭐️",
    "Мій нейрончик від такої новини аж загорівся 🔥"
]
# Сюди можна додавати ще свої приколи!

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

            # Додаємо випадковий жарт/смайлик/вогник в prompt для креативу
            emoji = random.choice(EMOJIS)
            joke = random.choice(PIKA_JOKES) if random.random() < 0.2 else ""

            prompt = (
                f"Перепиши цю новину для Telegram-каналу іншими словами українською мовою, "
                f"зберігаючи суть, додай багато сучасних емодзі, справжні абзаци, "
                f"легку жартівливість. Мінімум 200 букв (без пробілів). "
                f"Не додавай закликів до коментарів або відгуків. "
                f"Підпис обовʼязково — {SIGNATURE} в самому кінці. "
                f"{joke}\nТекст тільки для Telegram, без заголовка. Ось новина:\n\n{source_text}"
            )
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.1,
                max_tokens=340,
            )
            news = response.choices[0].message.content.strip()
            news = news.rstrip(".")
            if not news.endswith(SIGNATURE):
                news = news + "\n\n" + SIGNATURE
            # Додаємо смайлик на початок поста, якщо GPT не додав
            if not any(e in news[:10] for e in EMOJIS):
                news = emoji + " " + news
            # Рахуємо тільки букви (без пробілів)
            news_symbols = len("".join([c for c in news if c.isalpha()]))
            if news_symbols >= MIN_SYMBOLS:
                return news
        return None
    except Exception as e:
        print(f"❌ OpenAI/News fetch error: {e}")
        return None

def generate_dalle_image(news_text):
    # Стиль рандомно: мем, вектор, айті, креатив
    styles = [
        "vector illustration", "digital art", "cyberpunk style", "funny meme", "pixel art",
        "3d render", "futuristic", "techno art", "cartoon", "realistic", "anime style"
    ]
    style = random.choice(styles)
    dalle_prompt = (
        f"Create a {style} for the topic: {news_text[:80]}."
        f" Make it modern, creative, colorful, and IT/AI themed."
    )
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt,
            n=1,
            size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        print(f"❌ DALL-E error: {e}")
        return None

def post_to_telegram(text, image_url=None):
    if image_url:
        bot.send_photo(TELEGRAM_CHANNEL_ID, image_url, caption=text)
        print(f"🖼️ [{datetime.datetime.now().strftime('%H:%M:%S')}] Картинка + пост надіслані!")
    else:
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

        # Кожне 8-ме повідомлення з DALL-E
        image_url = None
        if (post_count + 1) % 8 == 0:
            image_url = generate_dalle_image(post)
            if not image_url:
                print("❗ Не вдалося отримати картинку, надсилаю тільки текст.")
        post_to_telegram(post, image_url)
        history.add(post)
        save_history(history)
        post_count += 1

        delay = random_delay()
        print(f"⏳ Наступний пост через {delay // 60} хвилин.")
        time.sleep(delay)

if __name__ == "__main__":
    main()
