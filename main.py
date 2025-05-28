from keep_alive import keep_alive
keep_alive()
import os
import time
import random
import json
import requests
import datetime
import openai
from telebot import TeleBot

# --- Конфігурація ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
HISTORY_FILE = "post_history.json"
MAX_POSTS_PER_DAY = 30
POSTING_HOURS_START = 9
POSTING_HOURS_END = 21

client = openai.OpenAI()
bot = TeleBot(TELEGRAM_BOT_TOKEN)

EMOJIS = ["🔥", "💡", "🚀", "🤖", "✨", "⚡", "🦾", "🧠", "💻", "🦄", "🎉"]
STATIC_THEMES = [
    "AI-новинки", "фреймворки", "інсайди", "нові інструменти", "Google", "GitHub", "лайфхаки", "open-source",
    "ProductHunt", "Bun", "Deno", "Next.js", "Qwik", "Astro", "VS Code", "Copilot", "аналітика", "тренди"
]

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False)

def random_delay_times(n, start_hour, end_hour):
    # Повертає список затримок (у хвилинах) між постами протягом дня в довільному порядку
    total_minutes = (end_hour - start_hour) * 60
    points = sorted(random.sample(range(1, total_minutes), n-1))
    times = [points[0]] + [points[i]-points[i-1] for i in range(1, len(points))] + [total_minutes - points[-1]]
    return [int(t) for t in times]

def generate_post(history):
    prompt = (
        f"Згенеруй унікальну авторську новину для Telegram-каналу про IT, AI, програмування, "
        f"яку ще не було раніше. Використовуй стиль: я автор, пиши з абзацами, вставляй смайли типу {random.choice(EMOJIS)}, "
        f"тематика: {random.choice(STATIC_THEMES)}. Мова: українська. Мінімум 350 символів. "
        f"Не копіюй існуюче з мережі. Пост закінчуй підписом без пробілу: @zlyv_ai."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",  # або gpt-4o, якщо є доступ і оплата!
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.9,
        )
        post = resp.choices[0].message.content.strip()
        # Перевірка на мінімальну довжину та унікальність
        if len(post) < 350 or post in history:
            return None
        return post
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        return None

def generate_image(post):
    # Якщо хочеш, можна додати генерацію з DALL-E, або просто повертати None
    return None

def post_to_telegram(post, image_url=None):
    try:
        if image_url:
            bot.send_photo(TELEGRAM_CHANNEL_ID, image_url, caption=post)
        else:
            bot.send_message(TELEGRAM_CHANNEL_ID, post)
        print("✅ Пост надіслано в Telegram!")
    except Exception as e:
        print(f"❗ Telegram error: {e}")

def main():
    history = load_history()
    posting_times = random_delay_times(MAX_POSTS_PER_DAY, POSTING_HOURS_START, POSTING_HOURS_END)
    print("🕒 Розклад на сьогодні:", posting_times)
    for idx, delay in enumerate(posting_times):
        post = None
        attempts = 0
        # Пробуємо 3 рази отримати унікальний пост
        while not post and attempts < 3:
            post = generate_post(history)
            attempts += 1
        if not post:
            print(f"❗ [{idx+1}] Не вдалося отримати новий пост, скипаємо.")
        else:
            image_url = generate_image(post) if random.random() < 0.3 else None
            post_to_telegram(post, image_url)
            history.add(post)
            save_history(history)
            print(f"✅ [{datetime.datetime.now().strftime('%H:%M:%S')}] Пост {idx+1}/{MAX_POSTS_PER_DAY} надіслано!")
        if idx < len(posting_times)-1:
            print(f"Наступний пост через {delay} хвилин.")
            time.sleep(delay * 60)

if __name__ == "__main__":
    while True:
        main()
        # На наступний день можна запустити main() з новими налаштуваннями
        print("День завершено! Чекаю до наступного старту.")
        time.sleep(60 * 60 * 3)  # чекати 3 години до наступної доби
