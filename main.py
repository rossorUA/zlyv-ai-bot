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
    "open-source", "ProductHunt", "Bun", "Deno", "Next.js", "Qwik", "Astro", "VS Code",
    "Copilot", "аналітика", "тренди", "DevTools", "Linux", "API", "Cloud", "ML"
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
        print(f"[DEBUG] Статус код: {resp.status_code}")
        data = resp.json()
        for hit in data.get("hits", []):
            if hit.get("title") and hit.get("url"):
                news.append({"title": hit["title"], "url": hit["url"]})
        random.shuffle(news)
        print(f"[DEBUG] Новин зібрано: {len(news)}")
    except Exception as e:
        print(f"[ERROR] fetch_fresh_news: {e}")
    return news

def paraphrase_text(title, url):
    # Щоб зробити пости різними, підкидаємо ідею для GPT
    extra = ""
    if random.random() < 0.33:
        extra = "\n" + random.choice(EXTRA_IDEAS)
    prompt = (
        "Ти — редактор Telegram-каналу для айтішників. Пиши українською мовою! "
        "На основі цього заголовку і посилання створи унікальний, авторський, легкий, неофіційний і веселий пост для Telegram, обсягом 250–350 символів (але не менше 250!). "
        "Не копіюй просто заголовок, не вигадуй фейкових фактів, пиши цікаво, додавай інтригу, прикол, мем, лайфхак або короткий аналіз. "
        "Додавай смайли всередині чи наприкінці, але не завершуй питанням і не використовуй банальні закінчення."
        f"\nОсь новина:\n{title}\n{url}{extra}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=1.4
        )
        text = response.choices[0].message.content.strip()
        # Якщо текст занадто довгий, обрізаємо до MAX_POST_LEN
        if len(text) > MAX_POST_LEN:
            text = text[:MAX_POST_LEN-1] + "…"
        # Якщо занадто короткий — додаємо випадковий мем
        if len(text) < MIN_POST_LEN:
            text += " " + random.choice(MEME_LINES)
        return text
    except Exception as e:
        print(f"[ERROR] paraphrase_text: {e}")
        return title  # fallback

def should_send_image():
    # Кожен 4-7 пост - з картинкою
    return random.randint(1, 6) == 3

def generate_caption(news, emojis):
    theme = random.choice(STATIC_THEMES)
    emoji = random.choice(EMOJIS)
    intro = f"{emoji} {theme.upper()}"
    text = paraphrase_text(news["title"], news["url"])
    # Додаємо мемний абзац через раз
    if random.random() < 0.45:
        text += "\n\n" + random.choice(MEME_LINES)
    # Додаємо ще емодзі у кінець або середину
    if random.random() < 0.5:
        text += " " + random.choice(EMOJIS)
    return f"{intro}\n\n{text}\n{SIGNATURE}"

def generate_ai_image(news):
    # Генеруємо малюнок через OpenAI DALL-E (або робимо мем/банер на тему новини)
    try:
        prompt = f"{news['title']}, trending, digital art, bright colors, vector illustration"
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
            caption = generate_caption(news, EMOJIS)
            try:
                # Випадково додаємо малюнок (раз на кілька постів)
                if should_send_image():
                    img_url = generate_ai_image(news)
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
