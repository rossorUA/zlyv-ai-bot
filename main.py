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
POSTING_HOURS_END = 24  # до 00:00

MIN_POST_LEN = 100   # Можеш змінити на 250 якщо треба суворо
MAX_POST_LEN = 350

HISTORY_FILE = "post_history.json"
EMOJIS = [
    '🔥', '🤖', '🦾', '🚀', '🧠', '✨', '💡', '😎', '🎉', '🌟', '📱', '🛠', '👾',
    '📊', '💻', '📢', '⚡️', '👨‍💻', '😏', '🥸', '🔮', '🕹️', '🦉', '🎲', '🧩', '🧑‍💻'
]

MEME_LINES = [
    "Пиши, якщо вже юзаєш це в продакшн 😅",
    "З такою новиною навіть понеділок не страшний 💪",
    "Залипай за компом – і не забудь зробити каву ☕️",
    "Відклади мишку, час апгрейднути мозок 🧠",
    "В нашому каналі тільки реально свіже, без корпоративної води 🥤",
    "Якщо дочитав – ти реально шариш 😉",
    "З таким апдейтом навіть код рев’ю здається легким 👀",
    "Фух, ну це вже next level! 🚀",
    "Не забувай: код фіксить баги, а новини — настрій! 😏",
    "Читаєш таке – і сам собі DevOps 🦉",
    "Хто не слідкує за трендами — той дебажить продакшн 😂"
]

EXTRA_IDEAS = [
    "Лайфхак: не чекай апдейту — тестуй одразу! 🦾",
    "Коротко: розробники вже це імплементують у продакшн.",
    "Бонус: швидкий тул для автоматизації – зекономить час кожному деву.",
    "Реальні кейси вже на GitHub. 🔥"
]

SIGNATURE = "\n@zlyv_ai"

IT_KEYWORDS = [
    "ai", "ml", "github", "python", "node", "javascript", "js", "typescript",
    "dev", "open source", "framework", "cloud", "linux", "tool", "api", "software",
    "release", "launch", "update", "feature", "docker", "kubernetes", "app", "react",
    "go", "java", "c++", "cpp", "data", "postgres", "sql", "macos", "windows",
    "openai", "deepmind", "gemini", "bard", "neural", "model", "gpt", "huggingface"
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
        resp = requests.get("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=80", timeout=10)
        data = resp.json()
        for hit in data.get("hits", []):
            if hit.get("title") and hit.get("url"):
                title = hit["title"].lower()
                # Суворий фільтр по ключових IT словах, і тільки останні новини
                if any(kw in title for kw in IT_KEYWORDS):
                    news.append({"title": hit["title"], "url": hit["url"]})
        random.shuffle(news)
    except Exception as e:
        print(f"[ERROR] fetch_fresh_news: {e}")
    return news

def extend_to_min_length(text, min_len=MIN_POST_LEN, max_len=MAX_POST_LEN):
    unique_memes = [x for x in MEME_LINES + EXTRA_IDEAS if x not in text]
    i = 0
    while len(text) < min_len and i < len(unique_memes):
        addition = " " + unique_memes[i]
        if len(text) + len(addition) > max_len:
            break
        text += addition
        i += 1
    if len(text) > max_len:
        last_space = text.rfind(' ', 0, max_len)
        if last_space == -1:
            last_space = max_len
        text = text[:last_space] + "…"
    return text.strip()

def clean_ending(text):
    last_word = text.strip().split()[-1].strip('.').strip('…').lower() if text.strip().split() else ''
    if last_word in BAD_ENDINGS or text.strip().endswith('…'):
        text = text.rstrip('…').rstrip('.') + ".\n\n" + random.choice(MEME_LINES)
    return text

def it_is_very_news(text):
    # Перевірка що в пості є ІТ-слова, і немає побуту, життєвих тем, відсилок на Маска, Meta тощо
    bad = ['ілон', 'маск', 'марс', 'тесла', 'meta', 'facebook', 'apple', 'google play', 'samsung', 'королева', 'трамп', 'політика', 'вірус', 'covid', 'health', 'енергія', 'сонце', 'марсіанин', 'астронавт']
    lower = text.lower()
    if any(b in lower for b in bad):
        return False
    # Має бути хоча б одне з IT_KEYWORDS
    return any(kw in lower for kw in IT_KEYWORDS)

def paraphrase_text(title, url):
    extra = ""
    if random.random() < 0.3:
        extra = "\n" + random.choice(EXTRA_IDEAS)
    prompt = (
        "Ти — редактор Telegram-каналу для айтішників. Пиши тільки українською! "
        "Використовуй велику і малу літери, не копіюй заголовок! "
        "Візьми цю новину і напиши конкретно по суті, що саме вийшло нового, яка головна фіча, що це дає розробникам або AI-ком’юніті, без філософії. "
        "Не згадуй сайти, бренди, Elon Musk, політику, Meta, не вставляй підписки і рекламу, без води і не загальний життєвий пост! "
        "Пиши у 2 абзацах, використовуй emoji. Мінімум 100 символів. "
        f"\nОсь новина:\n{title}{extra}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=350,
            temperature=1.0
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'(канал|сайт|реєстрац|підпис|telegram|tg|читайте|деталі|докладніше|читай|дивися|дивись|клік|приєднуй|слідкуй)', '', text, flags=re.I)
        text = re.sub(r'\n+', '\n', text)
        text = text.replace('  ', ' ')
        text = extend_to_min_length(text, min_len=MIN_POST_LEN, max_len=MAX_POST_LEN)
        if '\n' not in text:
            words = text.split()
            if len(words) > 32:
                text = ' '.join(words[:len(words)//2]) + '\n\n' + ' '.join(words[len(words)//2:])
        text = clean_ending(text)
        if all(e not in text for e in EMOJIS):
            text += " " + random.choice(EMOJIS)
        # Гарантуємо перевірку на IT та AI тематику!
        if not it_is_very_news(text):
            raise Exception("Не айті новина, фільтр!")
        return text.strip()
    except Exception as e:
        print(f"[ERROR] paraphrase_text: {e}")
        return None  # Якщо поганий пост — не відправляти

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
