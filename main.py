from keep_alive import keep_alive
import os
import time
import random
import requests
from telebot import TeleBot
from bs4 import BeautifulSoup


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

bot = TeleBot(TOKEN)
posted_texts = set()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
}


def fetch_posts():
    url = "https://neural.love/blog"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("article")

    posts = []
    for article in articles:
        text = article.get_text(separator=" ", strip=True)
        text = text.replace("\n", " ").strip()

        if 280 <= len(text) <= 450 and text not in posted_texts:
            formatted_text = format_post(text)
            posts.append(formatted_text)

    return posts


def format_post(text):
    # Додай абзаци та підпис каналу
    parts = text.split(". ")
    if len(parts) > 1:
        half = len(parts) // 2
        text = ". ".join(parts[:half]) + ".\n\n" + ". ".join(parts[half:])
    return text.strip() + "\n\n@zlyv_ai"


def post_to_telegram():
    posts = fetch_posts()
    if posts:
        post = random.choice(posts)
        posted_texts.add(post)
        bot.send_message(CHANNEL_ID, post)
        print("✅ Post sent")
    else:
        print("⚠️ No new unique posts found.")


if __name__ == '__main__':
    while True:
        post_to_telegram()
        time.sleep(600)  # 10 хвилин
