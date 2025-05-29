import os
import time
import random
import json
import requests
from telebot import TeleBot
from datetime import datetime

# Конфігурація
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
HISTORY_FILE = "post_history.json"
MAX_POSTS_PER_DAY = 30
POSTING_HOURS_START = 9
POSTING_HOURS_END = 21
EMOJIS = ["🔥", "🤖", "🚀", "💡", "✨", "😎", "🎉", "🦾", "🧠", "📢", "🌟", "💥", "⚡️", "📈", "🤩", "🪄"]
STATIC_THEMES = [
    "AI-новинки", "нейромережа", "інсайди", "нові інструменти", "Google", "GitHub", "фішки для програмістів",
    "свіжі релізи", "лайфхаки", "open-source", "ProductHunt", "Bun", "Deno", "Next.js", "Qwik", "Astro", "VS Code",
    "Copilot", "аналітика", "тренди"
]

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
    # Використовуємо HackerNews API як приклад (можна міняти)
    try:
        res = requests.get("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=50").json()
        return [hit['title'] + "\n" + hit['url'] for hit in res['hits']]
    except Exception as e:
        print("Помилка при отриманні новин:", e)
        return []

def rewrite_human(text):
    # Дуже примітивний перефраз — можна замінити своїм
    phrases = [
        "А ось і свіжа новина для тебе:", "Слухай це! ", "Тільки но виринуло:", "Справжня бомба: ",
        "Вперше у твоїй стрічці:", "Не прогав! ", "Прямо зараз:"
    ]
    return random.choice(phrases) + text

def send_post(text, with_image=False):
    # Додаємо емодзі й підпис
    emoji = random.choice(EMOJIS)
    post = f"{emoji} {text.strip()}\n@zlyv_ai"
    if with_image:
        # Додаємо картинку + водяний знак (простий спосіб – тут зображення з URL або своє PNG з логотипом)
        # Для генерації картинки — інтегрувати DALL·E або брати випадковий placeholder
        photo_url = "https://placehold.co/600x400.png?text=ZLYV+AI"
        try:
            bot.send_photo(TELEGRAM_CHANNEL_ID, photo_url, caption=post)
        except Exception as e:
            print("Помилка надсилання зображення:", e)
    else:
        try:
            bot.send_message(TELEGRAM_CHANNEL_ID, post)
        except Exception as e:
            print("Помилка надсилання повідомлення:", e)

def main():
    print("Бот стартував!")
    history = load_history()
    posts_today = 0
    last_post_time = None

    while True:
        now = datetime.now()
        hour = now.hour

        # Від 9:00 до 21:00 і максимум 30 постів
        if hour >= POSTING_HOURS_START and hour <= POSTING_HOURS_END and posts_today < MAX_POSTS_PER_DAY:
            fresh_news = fetch_fresh_news()
            random.shuffle(fresh_news)
            found = False

            for raw_news in fresh_news:
                news_id = raw_news[:100]  # Для унікальності — перші 100 символів
                if news_id not in history:
                    # Сгенеруй пост у стилі "живої" людини
                    theme = random.choice(STATIC_THEMES)
                    text = rewrite_human(raw_news)
                    # Тримайся в межах 200-250 символів:
                    text = text[:240] + "…" if len(text) > 250 else text
                    # Emoji і підпис додаються у send_post

                    # 1 з 8 — з картинкою
                    with_image = (posts_today % random.randint(6, 9) == 0)
                    send_post(f"#{theme}\n{text}", with_image=with_image)
                    print(f"Відправлено пост: {text}")
                    history.add(news_id)
                    save_history(history)
                    posts_today += 1
                    found = True
                    break

            if not found:
                print("Нових новин не знайдено.")
            
            # Час до наступного поста — рандомно від 10 до 60 хвилин
            sleep_min = random.randint(10, 60)
            print(f"Затримка перед наступним постом: {sleep_min} хв.")
            time.sleep(sleep_min * 60)
        else:
            # Спимо 10 хв якщо ніч або перевищено ліміт
            time.sleep(600)
            if hour == 0:
                posts_today = 0  # Оновлення ліміту опівночі

if __name__ == "__main__":
    main()
