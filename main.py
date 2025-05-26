import telebot
import time
import random
from datetime import datetime
from keep_alive import keep_alive
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

bot = telebot.TeleBot(TOKEN)

POSTS = [
    "GPT-4o тепер перебиває тебе вголос. OpenAI тестує нову голосову модель, яка не просто говорить, а здатна розпізнати, коли користувач починає говорити — й “перебити” його. Це дозволяє ШІ реагувати як реальний співрозмовник з емоціями та плавністю.\n@zlyv_ai",
    "Textual — новий фреймворк на Python для створення TUI-додатків у терміналі з логікою як у фронтенду. Він дає змогу створювати компоненти інтерфейсу як у React, але прямо в CLI.\n@zlyv_ai",
    "Meta показала ШІ, який читає думки з EEG-даних. Модель здатна реконструювати прості образи на основі мозкової активності. Це ще не телепатія, але дуже близько.\n@zlyv_ai",
    "Google DeepMind представив RT-2.5 — мультимодальну модель, яка інтерпретує відео як серіальні епізоди, розуміючи не просто кадри, а цілісні сцени та мотивацію.\n@zlyv_ai"
]

used_posts = []

def get_next_post():
    global used_posts
    if not used_posts:
        used_posts = POSTS.copy()
        random.shuffle(used_posts)
    return used_posts.pop()

def post_loop():
    while True:
        post = get_next_post()
        print("\n🌀 Обрано пост:")
        print(post)
        try:
            bot.send_message(CHANNEL_ID, post)
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"✅ Надіслано в {CHANNEL_ID} о {current_time}")
        except Exception as e:
            print("❌ Помилка:", e)
        print("⏳ Сплю 10 хвилин...\n")
        time.sleep(600)

if __name__ == "__main__":
    keep_alive()
    print("✅ Бот запущено. Надсилаю перший пост...\n")
    bot.send_message(CHANNEL_ID, "⚡ Старт автозливу. Далі — кожні 10 хв.\n@zlyv_ai")
    post_loop()
