import telebot
import os
import yt_dlp
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = '8390506713:AAGKlZcg0IrG99FoNM890tB0W0gNs2tKuvs'
CHANNEL_ID = '@reelsrazyob'

bot = telebot.TeleBot(BOT_TOKEN)

def download_reel(reel_url):
    try:
        ydl_opts = {
            'outtmpl': 'reel_video.%(ext)s',
            'format': 'mp4',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([reel_url])
            info = ydl.extract_info(reel_url, download=False)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне ссылку на Instagram Reel, и я опубликую его в канале @reelsrazyob.")

@bot.message_handler(func=lambda message: True)
def handle_reel_link(message):
    if 'instagram.com/reel/' in message.text or 'instagram.com/p/' in message.text:
        processing_msg = bot.reply_to(message, "🔄 Скачиваю рилс...")
        
        video_path = download_reel(message.text)
        
        if video_path and os.path.exists(video_path):
            bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text="📤 Отправляю в канал...")
            
            try:
                with open(video_path, 'rb') as video:
                    bot.send_video(CHANNEL_ID, video, caption="Новый рилс! 📹")
                bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text="✅ Рилес успешно опубликован в канале!")
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text=f"❌ Ошибка при отправке: {e}")
            
            os.remove(video_path)
        else:
            bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text="❌ Не удалось скачать видео. Проверьте ссылку.")
    else:
        bot.reply_to(message, "Это не похоже на ссылку на Instagram Reel.")

def start_bot():
    logger.info("Запускаем бота...")
    while True:
        try:
            logger.info("Бот запущен и слушает сообщения...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            logger.info("Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == '__main__':
    start_bot()