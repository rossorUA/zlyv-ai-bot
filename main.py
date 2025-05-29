import os
import time
import random
import json
import requests
from datetime import datetime, timedelta
from telebot import TeleBot
import openai
from PIL import Image, ImageDraw, ImageFont

# --- Конфіги ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
HISTORY_FILE = "post_history.json"
MAX_POSTS_PER_DAY = 30
POSTING_HOURS_START = 9
POSTING_HOURS_END = 21
LOGO_PATH = "logo_zlyv_ai.png"   # твій прозорий логотип

openai.api_key = OPENAI_API_KEY
bot = TeleBot(TELEGRAM_BOT_TOKEN)

EMOJIS = ["🔥", "🤖", "🧠", "😎", "💡", "🎉", "🚀", "🦾", "⚡", "🦾", "🤘", "👾"]
STATIC_TOPICS = [
    "AI-новинки", "нейромережа", "інсайди", "нові інструменти", "Google", "GitHub",
    "фреймворки", "open-source", "ProductHunt", "Bun", "Deno", "Next.js", "Qwik",
    "Astro", "VS Code", "Copilot", "аналітика", "тренди"
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
    # Тут парсимо гарячі новини (Hacker News + GitHub Trending + Product Hunt)
    news = []
    try:
        hn = requests.get("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=20").json()
        for hit in hn['hits']:
            news.append({"title": hit['title'], "url": hit['url'] or hit.get('story_url')})
    except: pass
    # Додаємо ще один парсер, наприклад GitHub Trending (можна додати інші)
    try:
        gh = requests.get("https://ghapi.huchen.dev/repositories?since=daily").json()
        for repo in gh[:15]:
            news.append({"title": repo['name'] + " — " + repo['description'], "url": repo['url']})
    except: pass
    return news

def paraphrase_text(text):
    # Перефразування у стилі автора
    prompt = f"Перепиши наступну новину живою мовою, коротко (200-250 символів), з емодзі та жартами, розбий на 2-3 абзаци. Стиль — як Ростислав із каналу 'Злив від ШІ':\n\n{text}\n\n"
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.88,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def add_logo_to_image(image_path, logo_path=LOGO_PATH):
    # Додаємо водяний знак у кут (малопомітно)
    base = Image.open(image_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")
    scale = int(min(base.size) * 0.18)
    logo = logo.resize((scale, scale))
    pos = (base.size[0]-scale-10, base.size[1]-scale-10)
    tmp = Image.new("RGBA", base.size)
    tmp.paste(logo, pos, logo)
    out = Image.alpha_composite(base, tmp)
    result_path = "final_"+os.path.basename(image_path)
    out.save(result_path)
    return result_path

def generate_dalle_image(prompt):
    # Створює і зберігає картинку через DALL-E
    dalle = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="url"
    )
    img_url = dalle['data'][0]['url']
    img_data = requests.get(img_url).content
    fname = "dalle_tmp.png"
    with open(fname, "wb") as f:
        f.write(img_data)
    return add_logo_to_image(fname)

def post_to_telegram(text, image_path=None):
    if image_path:
        with open(image_path, "rb") as img:
            bot.send_photo(TELEGRAM_CHANNEL_ID, img, caption=text)
    else:
        bot.send_message(TELEGRAM_CHANNEL_ID, text)

def main():
    history = load_history()
    posted_today = 0
    last_date = None
    while True:
        now = datetime.now()
        if POSTING_HOURS_START <= now.hour < POSTING_HOURS_END and posted_today < MAX_POSTS_PER_DAY:
            if last_date != now.date():
                posted_today = 0
                last_date = now.date()
            news = fetch_fresh_news()
            random.shuffle(news)
            for item in news:
                if posted_today >= MAX_POSTS_PER_DAY:
                    break
                key = item['title']
                if key in history or not item.get('title'):
                    continue
                text = paraphrase_text(item['title'])
                # Смайлики, абзаци, підпис
                text = f"{random.choice(EMOJIS)} {text}\n@zlyv_ai"
                image_ok = (random.randint(1, 9) == 5)  # кожне 7-9 рандомно — з картинкою
                if image_ok:
                    prompt = f"{item['title']}. Додай технологічний стиль, українською, хай буде крутий арт/мем/фото."
                    image_path = generate_dalle_image(prompt)
                    post_to_telegram(text, image_path)
                else:
                    post_to_telegram(text)
                history.add(key)
                posted_today += 1
                save_history(history)
                # Випадковий інтервал 15–50 хвилин
                time.sleep(random.randint(900, 3000))
        else:
            # Чекаємо до наступної години
            time.sleep(300)

if __name__ == "__main__":
    main()
