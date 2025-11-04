import telebot
import os
import requests
import re
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = '8390506713:AAGKlZcg0IrG99FoNM890tB0W0gNs2tKuvs'
CHANNEL_ID = '@reelsrazyob'

bot = telebot.TeleBot(BOT_TOKEN)

def download_reel(reel_url):
    """Упрощенная функция скачивания"""
    try:
        # Простая реализация через ddinstagram
        dd_url = reel_url.replace('www.instagram.com', 'www.ddinstagram.com')
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        response = session.get(dd_url, timeout=30)
        video_match = re.search(r'<video[^>]*src="([^"]+)"', response.text)
        
        if video_match:
            video_url = video_match.group(1)
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            
            video_response = session.get(video_url, stream=True, timeout=60)
            filename = "reel_video.mp4"
            
            with open(filename, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return filename
        return None
        
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь ссылку на Instagram Reel.")

@bot.message_handler(func=lambda message: True)
def handle_reel_link(message):
    if 'instagram.com/reel/' in message.text:
        msg = bot.reply_to(message, "🔄 Скачиваю...")
        
        video_path = download_reel(message.text)
        
        if video_path:
            bot.edit_message_text("📤 Отправляю...", message.chat.id, msg.message_id)
            
            try:
                with open(video_path, 'rb') as video:
                    bot.send_video(CHANNEL_ID, video, caption="Новый рилс! 📹")
                bot.edit_message_text("✅ Опубликовано!", message.chat.id, msg.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Ошибка: {e}", message.chat.id, msg.message_id)
            
            try:
                os.remove(video_path)
            except:
                pass
        else:
            bot.edit_message_text("❌ Не удалось скачать", message.chat.id, msg.message_id)

if __name__ == '__main__':
    logger.info("Бот запущен")
    bot.infinity_polling()
