import os
import time
import random
import json
import requests
import datetime
import openai
from telebot import TeleBot

# === Конфігурація ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HISTORY_FILE = "post_history.json"
MAX_POSTS_PER_DAY = 30
POSTING_HOURS_START = 9    # З 9:00
POSTING_HOURS_END = 21     # До 21:00

openai.api_key = OPENAI_API_KEY
bot = TeleBot(TELEGRAM_BOT_TOKEN)

EMOJIS = ["🔥", "🤖", "💡", "✨", "🚀", "🧠", "⚡", "📢", "🌟", "🦾", "💻", "😎", "😏", "😁", "🎉", "😮"]
# Теми автогенеруються автоматично, але можна додати свої
STATIC_THEMES = [
    "AI-новинки", "фреймворки", "інсайди", "нові інструменти", "Google", "GitHub", "меми для програмістів",
    "свіжі релізи", "лайфхаки", "open-source", "ProductHunt", "Bun, Deno, Next.js", "Qwik, Astro", "VS Code",
    "Copilot", "нейромережі", "аналітика", "тренди, які ще не в мейнстримі"
]

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False)

def fetch_fresh_news():
    # Беремо свіжі заголовки з кількох джерел. Можна додати ще.
    try:
        news = []
        # Hacker News (топ за день)
        hn = requests.get("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=20").json()
        for hit in hn['hits']:
            title = hit['title']
            url = hit['url'] or hit.get('story_url', '')
            if title and url:
                news.append(f"{title} ({url})")
        # Product Hunt (API є, тут просто фейковий парсер для прикладу)
        # news.append("Новий стартап на ProductHunt - OpenAI Tetris (https://www.producthunt.com/)")
        # GitHub Trending (можна додати справжній парсер через BeautifulSoup)
        return random.sample(news, min(5, len(news)))  # Беремо 5 випадкових новин
    except Exception as e:
        print("⚠️ Не вдалося отримати новини:", e)
        return []

def random_emoji():
    return random.choice(EMOJIS)

def generate_post(history):
    themes = STATIC_THEMES + fetch_fresh_news()
    theme = random.choice(themes)
    extra_humor = random.choice([
        "",
        "Доречі, айтішники — це маги XXI століття! " + random_emoji(),
        "Маю думку: без сміху тут не вижити " + random_emoji(),
        "Ще б кави... " + random_emoji(),
        "Всі баги — це фічі, просто ви ще не розібралися 😏"
    ])
    prompt = (
        f"Уяви, що ти — український айтішник-інсайдер, який пише унікальні авторські пости для Telegram-каналу про IT, AI, програмування, нові фреймворки. "
        f"Згенеруй унікальний, людяний, легкий, веселий, іноді з іронією та мемами пост українською мовою (мінімум 350 символів), про тему: {theme}. "
        f"Структуруй у 2-4 справжніх абзаци, без зайвих пустих рядків. Вставляй різні emoji, особливо вогники, смайли, сучасні іконки. "
        f"Завжди пиши від першої особи, жартуй, додавай власні коментарі, щоб було відчуття, що пише реальна людина. "
        f"Підпис @zlyv_ai одразу під текстом, без пробілу. Не повторюй минулі пости, придумай щось нове. "
        f"{extra_humor}"
    )
    # Генерація посту через GPT
    for _ in range(6):
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            temperature=1.1
        )
        post = resp.choices[0].message["content"].strip()
        post = post.replace("\n\n\n", "\n\n").replace(" @zlyv_ai", "\n@zlyv_ai").replace("\n @zlyv_ai", "\n@zlyv_ai")
        if post not in history and len(post) >= 340 and post.endswith("@zlyv_ai"):
            return post
    return None

def generate_image(post_text):
    try:
        img_prompt = (
            f"Згенеруй сучасну унікальну картинку у різному стилі (арт, вектор, digital, ілюстрація) до цього авторського айтішного поста: \"{post_text[:100]}...\". "
            f"Без жодного тексту на зображенні. Сюжет має підходити під зміст тексту."
        )
        dalle = openai.Image.create(
            prompt=img_prompt,
            n=1,
            size="1024x1024"
        )
        return dalle['data'][0]['url']
    except Exception as e:
        print("Не вдалося створити малюнок:", e)
        return None

def post_to_telegram(post_text, image_url=None):
    if image_url:
        img = requests.get(image_url).content
        with open("temp_image.png", "wb") as f:
            f.write(img)
        with open("temp_image.png", "rb") as photo:
            bot.send_photo(TELEGRAM_CHANNEL_ID, photo, caption=post_text)
        os.remove("temp_image.png")
    else:
        bot.send_message(TELEGRAM_CHANNEL_ID, post_text)

def make_posting_times():
    # Генеруємо 30 випадкових проміжків для публікацій на день
    minutes = (POSTING_HOURS_END - POSTING_HOURS_START) * 60
    points = sorted(random.sample(range(1, minutes-1), MAX_POSTS_PER_DAY - 1))
    times = [points[0]] + [points[i] - points[i-1] for i in range(1, len(points))] + [minutes - points[-1]]
    return times

def wait_until(start_hour):
    now = datetime.datetime.now()
    if now.hour < start_hour:
        wake = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        delay = (wake - now).total_seconds()
        print(f"Зараз ніч — чекаємо до {start_hour}:00 ({int(delay//60)} хв)")
        time.sleep(delay)

def main():
    while True:
        now = datetime.datetime.now()
        if now.hour < POSTING_HOURS_START or now.hour >= POSTING_HOURS_END:
            wait_until(POSTING_HOURS_START)
        posting_times = make_posting_times()
        print(f"Графік на сьогодні: {posting_times}")
        history = load_history()
        for idx, delay in enumerate(posting_times):
            post = None
            while not post:
                post = generate_post(history)
            # Випадковий шанс додати малюнок (25-35%)
            image_url = generate_image(post) if random.random() < random.uniform(0.25, 0.35) else None
            post_to_telegram(post, image_url)
            print(f"✅ [{datetime.datetime.now().strftime('%H:%M:%S')}] Пост {idx+1}/30 надіслано!")
            history.add(post)
            save_history(history)
            if idx < len(posting_times)-1:
                print(f"Наступний пост через {delay} хвилин.")
                time.sleep(delay * 60)
        print("Всі пости на сьогодні надіслані. Чекаємо до завтра!")
        wait_until(POSTING_HOURS_START)

if __name__ == "__main__":
    main()
