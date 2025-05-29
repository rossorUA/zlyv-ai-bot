from keep_alive import keep_alive
keep_alive()

import os
import time
import random
import json
import requests
import re
from datetime import datetime
import openai
from telebot import TeleBot

# --- Конфіг ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

MAX_POSTS_PER_DAY = 30
POSTING_HOURS_START = 9
POSTING_HOURS_END = 24

MIN_POST_LEN = 100
MAX_POST_LEN = 350

HISTORY_FILE = "post_history.json"
EMOJIS = [
    '🔥', '🤖', '🦾', '🚀', '🧠', '✨', '💡', '😎', '🎉', '🌟', '📱', '🛠', '👾',
    '📊', '💻', '📢', '⚡️', '👨‍💻', '😏', '🥸', '🔮', '🕹️', '🦉', '🎲', '🧩', '🧑‍💻'
]
SIGNATURE = "\n@zlyv_ai"

IT_KEYWORDS = [
    "ai", "ml", "github", "python", "node", "javascript", "js", "typescript",
    "dev", "open source", "framework", "cloud", "linux", "tool", "api", "software",
    "release", "launch", "update", "feature", "docker", "kubernetes", "app", "react",
    "go", "java", "c++", "cpp", "data", "postgres", "sql", "macos", "windows",
    "openai", "deepmind", "gemini", "bard", "neural", "model", "gpt", "huggingface",
    "plugin", "sdk", "cli", "бібліотека", "утиліта", "middleware", "package"
]

# Фільтр тільки по НОВИХ ІНСТРУМЕНТАХ, БІБЛІОТЕКАХ, АІ/API/FW, релізах
IT_STRICT_MUSTHAVE = [
    "новий інструмент", "бібліотека", "api", "оновлення", "додаток", "утиліта", "open-source",
    "реліз", "release", "plugin", "sdk", "cli", "feature", "framework", "ai модель", "ai tool",
    "ml tool", "dev tool", "developer tool", "ai api", "library", "middleware", "package"
]

BAD_ENDINGS = [
    "можливість", "пристрій", "новина", "реліз", "версія", "фіча", "апдейт",
    "оновлення", "випуск", "інструмент", "доповнення", "модуль", "додаток", "…"
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
    try:
        resp = requests.get("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=120", timeout=10)
        data = resp.json()
        for hit in data.get("hits", []):
            if hit.get("title") and hit.get("url"):
                title = hit["title"].lower()
                if any(kw in title for kw in IT_KEYWORDS):
                    news.append({"title": hit["title"], "url": hit["url"]})
        random.shuffle(news)
    except Exception as e:
        print(f"[ERROR] fetch_fresh_news: {e}")
    return news

def is_really_technical(text):
    # Пост тільки про інструмент/бібліотеку/AI/API/плагін — без філософії, Марса, Meta, IT-лайфстайлу
    lower = text.lower()
    if not any(mh in lower for mh in IT_STRICT_MUSTHAVE):
        return False
    bad = ['ілон', 'маск', 'meta', 'facebook', 'apple', 'королева', 'трамп', 'політика', 'covid', 'енергія', 'марс', 'тесла', 'життя', 'здоров\'я', 'lifestyle', 'planet', 'новина дня']
    if any(b in lower for b in bad):
        return False
    # Якщо нема короткого пояснення — не публікувати
    if not re.search(r"(для |яка|дозволяє|щоб |як |що |api|інструмент|бібліотека|утиліта|framework|plugin|sdk)", lower):
        return False
    return True

def extend_to_min_length(text, min_len=MIN_POST_LEN, max_len=MAX_POST_LEN):
    if len(text) < min_len:
        text += " " + random.choice(EMOJIS)
    if len(text) > max_len:
        last_space = text.rfind(' ', 0, max_len)
        if last_space == -1:
            last_space = max_len
        text = text[:last_space] + "…"
    return text.strip()

def clean_ending(text):
    last_word = text.strip().split()[-1].strip('.').strip('…').lower() if text.strip().split() else ''
    if last_word in BAD_ENDINGS or text.strip().endswith('…'):
        text = text.rstrip('…').rstrip('.') + "."
    return text

def paraphrase_text(title, url):
    prompt = (
        "Ти — редактор Telegram-каналу для айтішників. Пиши тільки українською! "
        "Без жодної води, тільки новий інструмент, бібліотека, фреймворк, API, AI-продукт, реліз чи апдейт. "
        "Опиши для чого цей продукт, для кого, головну фічу або API, як юзати (1-2 речення), максимум конкретики. "
        "Не згадуй бренди, людей, політику, не пиши філософію, тільки технічна суть. "
        "Пиши у 1-2 абзацах, з emoji, мінімум 100 символів, закінчуй реченням, не обривай пост!"
        "\nОсь новина:\n" + title
    )
    for _ in range(4):  # до 4 спроб
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=350,
                temperature=0.8
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r'http\S+', '', text)
            text = re.sub(r'#\w+', '', text)
            text = re.sub(r'\n+', '\n', text)
            text = text.replace('  ', ' ')
            text = extend_to_min_length(text, min_len=MIN_POST_LEN, max_len=MAX_POST_LEN)
            if all(e not in text for e in EMOJIS):
                text += " " + random.choice(EMOJIS)
            text = clean_ending(text)
            if not is_really_technical(text):
                continue  # тільки реальні інструменти, жодної води
            if not text.endswith('.') and not text.endswith('!') and not text.endswith('?'):
                text += "."
            if len(text) < MIN_POST_LEN:
                continue
            return text.strip()
        except Exception as e:
            print(f"[ERROR] paraphrase_text: {e}")
            continue
    return None

def generate_caption(news):
    text = paraphrase_text(news["title"], news["url"])
    if not text:
        return None
    return f"{text}\n{SIGNATURE}"

def post_news():
    history = load_history()
    news_list = fetch_fresh_news()
    print(f"[DEBUG] Є {len(news_list)} новин")
    for news in news_list:
        print(f"[DEBUG] Перевіряю: {news['title']}")
        if news["title"] not in history and news["title"]:
            caption = generate_caption(news)
            if not caption:
                continue  # Пропуск поста, якщо фільтр не пройшов!
            try:
                bot.send_message(TELEGRAM_CHANNEL_ID, caption)
                print(f"[SUCCESS] Пост надіслано: {caption[:60]}")
                history.add(news["title"])
                save_history(history)
            except Exception as e:
                print(f"[ERROR] post_news: {e}")
            break
    else:
        print("[DEBUG] Нових новин для публікації немає.")

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
