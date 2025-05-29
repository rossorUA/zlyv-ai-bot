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
POSTING_HOURS_END = 24   # <- До 00:00

MIN_POST_LEN = 250
MAX_POST_LEN = 350

HISTORY_FILE = "post_history.json"
EMOJIS = [
    '🔥', '🤖', '🦾', '🚀', '🧠', '✨', '💡', '😎', '🎉', '🌟', '📱', '🛠', '👾',
    '📊', '💻', '📢', '⚡️', '👨‍💻', '😏', '🥸', '🔮', '🕹️', '🦉', '🎲', '🧩', '🧑‍💻'
]
SIGNATURE = "\n@zlyv_ai"

STATIC_THEMES = [
    "AI-новинки", "фреймворки", "інсайди", "нові інструменти", "Google", "GitHub", "лайфхаки",
    "open-source", "Bun", "Deno", "Next.js", "Qwik", "Astro", "VS Code",
    "Copilot", "аналітика", "тренди", "DevTools", "Linux", "API", "Cloud", "ML"
]

STYLE_PROMPTS = [
    "pixel art, vibrant, detailed",
    "vector illustration, flat, modern, bright",
    "photo-realistic, realistic lighting, tech workspace",
    "3d render, colorful, modern, shiny",
    "minimalist, clean, sharp, IT design",
    "retro computer art, 90s style",
    "mem-style, fun, ironic"
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
    "Бонус: маленький лайфхак — виділи 10 хвилин на нову фічу! 💡",
    "Тримай інтригу: наступна новина вже гріє повітря в інтернеті 😉",
    "Короткий аналіз: розробники вже тестують це в своїх pet-проектах! 🧩",
    "Мем дня: 'Коли хотів переписати legacy-код — а отримав новий фреймворк!' 🤣",
    "Fun fact: в 2025 році такі штуки будуть must-have для кожного девелопера! 🚀",
    "Жарт: справжній dev не шукає баги — баги самі знаходять його! 🥸"
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
        resp = requests.get("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=50", timeout=10)
        data = resp.json()
        for hit in data.get("hits", []):
            if hit.get("title") and hit.get("url"):
                news.append({"title": hit["title"], "url": hit["url"]})
        random.shuffle(news)
    except Exception as e:
        print(f"[ERROR] fetch_fresh_news: {e}")
    return news

def paraphrase_text(title, url):
    extra = ""
    if random.random() < 0.33:
        extra = "\n" + random.choice(EXTRA_IDEAS)
    prompt = (
        "Ти — редактор українського Telegram-каналу для айтішників. Пиши тільки українською. "
        "Твоя задача: взяти тему новини та створити унікальний, авторський, легкий, неофіційний і веселий пост (250–350 символів), без заголовків, без теми, не згадуючи сайти, бренди, посилання, хештеги чи заклики до реєстрації. "
        "Не копіюй заголовок, не вигадуй неіснуючі сервіси, не вставляй рекламу чи підписки. "
        "Просто зроби короткий авторський огляд/думку/реакцію на новинку – без реклами, без питань у кінці, без банальних фраз і без назв сайтів. "
        "Додавай смайли, легкий гумор, лайфхак, прикол, короткий аналіз, але тільки по темі IT, AI, програмування."
        " Ось новина:\n"
        f"{title}\n{extra}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=1.35
        )
        text = response.choices[0].message.content.strip()
        # Чистка тексту від брендів/посилань/спаму
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        text = re.sub(r'(канал|сайт|реєстрац|підпис|telegram|tg|читайте|деталі|докладніше|читай|дивися|дивись|клік|приєднуй|слідкуй)', '', text, flags=re.I)
        text = re.sub(r'\n+', '\n', text)
        text = text.replace('  ', ' ')
        if len(text) > MAX_POST_LEN:
            text = text[:MAX_POST_LEN-1] + "…"
        if len(text) < MIN_POST_LEN:
            text += " " + random.choice(MEME_LINES)
        return text.strip()
    except Exception as e:
        print(f"[ERROR] paraphrase_text: {e}")
        return title  # fallback

def random_style_prompt(theme):
    base = random.choice(STYLE_PROMPTS)
    topic = theme.lower()
    full = f"{base}, theme: {topic}, trending, digital art, no text, high detail, modern"
    return full

def should_send_image():
    # Кожен 3-5 пост – з малюнком
    return random.randint(1, 5) == 3

def generate_caption(news, emojis):
    # Без заголовків і тем
    text = paraphrase_text(news["title"], news["url"])
    # Мемний абзац іноді
    if random.random() < 0.45:
        text += "\n\n" + random.choice(MEME_LINES)
    # Емодзі ще у кінець або середину
    if random.random() < 0.5:
        text += " " + random.choice(EMOJIS)
    return f"{text}\n{SIGNATURE}", random.choice(STATIC_THEMES)

def generate_ai_image(news, theme):
    try:
        style_prompt = random_style_prompt(theme)
        prompt = f"{news['title']}, {style_prompt}"
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        print(f"[ERROR] generate_ai_image: {e}")
        return None

def post_news():
    history = load_history()
    news_list = fetch_fresh_news()
    print(f"[DEBUG] Є {len(news_list)} новин")
    for news in news_list:
        print(f"[DEBUG] Перевіряю: {news['title']}")
        if news["title"] not in history and news["title"]:
            caption, theme = generate_caption(news, EMOJIS)
            try:
                if should_send_image():
                    img_url = generate_ai_image(news, theme)
                    if img_url:
                        bot.send_photo(TELEGRAM_CHANNEL_ID, img_url, caption=caption)
                        print(f"[SUCCESS] Пост із малюнком надіслано: {caption[:60]}")
                    else:
                        bot.send_message(TELEGRAM_CHANNEL_ID, caption)
                        print(f"[SUCCESS] Пост без малюнка надіслано: {caption[:60]}")
                else:
                    bot.send_message(TELEGRAM_CHANNEL_ID, caption)
                    print(f"[SUCCESS] Пост без малюнка надіслано: {caption[:60]}")
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
