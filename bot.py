import telebot
import os
import requests
import re
import time
import logging
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = '8390506713:AAGKlZcg0IrG99FoNM890tB0W0gNs2tKuvs'
CHANNEL_ID = '@reelsrazyob'

bot = telebot.TeleBot(BOT_TOKEN)

# Переменная для контроля работы бота
bot_running = False

def download_reel(reel_url):
    try:
        logger.info(f"Пытаемся скачать рилс: {reel_url}")
        
        # Сначала пробуем метод с ddinstagram
        result = download_via_ddinstagram(reel_url)
        if result:
            logger.info("Успешно скачано через ddinstagram")
            return result
        
        # Если не сработало, пробуем ssstik.io
        logger.info("ddinstagram не сработал, пробуем ssstik.io...")
        result = download_via_ssstik(reel_url)
        if result:
            logger.info("Успешно скачано через ssstik.io")
            return result
        
        # Если не сработало, пробуем snaptik.app
        logger.info("ssstik.io не сработал, пробуем snaptik.app...")
        result = download_via_snaptik(reel_url)
        if result:
            logger.info("Успешно скачано через snaptik.app")
            return result
            
        logger.error("Все методы не сработали")
        return None
        
    except Exception as e:
        logger.error(f"Общая ошибка при скачивании: {e}")
        return None

def download_via_ddinstagram(reel_url):
    """Метод с заменой на ddinstagram"""
    try:
        # Заменяем домен на ddinstagram
        ddinstagram_url = reel_url.replace('www.instagram.com', 'www.ddinstagram.com')
        logger.info(f"Пробуем ddinstagram URL: {ddinstagram_url}")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        })
        
        response = session.get(ddinstagram_url, timeout=30)
        response.raise_for_status()
        
        # Ищем видео
        video_url_match = re.search(r'<video[^>]*src="([^"]+)"', response.text)
        if video_url_match:
            video_url = video_url_match.group(1)
            
            # Если URL относительный, делаем его абсолютным
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            elif video_url.startswith('/'):
                video_url = 'https://www.ddinstagram.com' + video_url
            
            logger.info(f"Найдено видео: {video_url}")
            
            # Скачиваем видео
            video_response = session.get(video_url, stream=True, timeout=60)
            video_response.raise_for_status()
            
            filename = "reel_video_ddinstagram.mp4"
            with open(filename, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                logger.info(f"Видео успешно скачано, размер: {os.path.getsize(filename)} байт")
                return filename
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка в ddinstagram: {e}")
        return None

def download_via_ssstik(reel_url):
    """Скачивание через ssstik.io"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
        
        ssstik_url = "https://ssstik.io"
        response = session.get(ssstik_url, timeout=30)
        response.raise_for_status()
        
        token_match = re.search(r'name="tt" value="([^"]+)"', response.text)
        if not token_match:
            return None
        
        token = token_match.group(1)
        
        download_url = "https://ssstik.io/abc?url=dl"
        data = {
            "id": reel_url,
            "locale": "en",
            "tt": token
        }
        
        response = session.post(download_url, data=data, timeout=30)
        response.raise_for_status()
        
        video_url_match = re.search(r'href="(https[^"]+\.mp4[^"]*)"', response.text)
        if not video_url_match:
            return None
        
        video_url = video_url_match.group(1)
        
        video_response = session.get(video_url, stream=True, timeout=60)
        video_response.raise_for_status()
        
        filename = "reel_video_ssstik.mp4"
        with open(filename, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            return filename
        else:
            return None
            
    except Exception as e:
        logger.error(f"Ошибка в ssstik: {e}")
        return None

def download_via_snaptik(reel_url):
    """Скачивание через snaptik.app"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
        
        snaptik_url = "https://snaptik.app"
        response = session.get(snaptik_url, timeout=30)
        response.raise_for_status()
        
        token_match = re.search(r'name="token" value="([^"]+)"', response.text)
        if not token_match:
            return None
        
        token = token_match.group(1)
        
        api_url = "https://snaptik.app/abc2.php"
        data = {
            "url": reel_url,
            "token": token
        }
        
        response = session.post(api_url, data=data, timeout=30)
        response.raise_for_status()
        
        video_url_match = re.search(r'"download_url":"([^"]+)"', response.text)
        if video_url_match:
            video_url = video_url_match.group(1).replace('\\', '')
            
            video_response = session.get(video_url, stream=True, timeout=60)
            video_response.raise_for_status()
            
            filename = "reel_video_snaptik.mp4"
            with open(filename, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return filename
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка в snaptik: {e}")
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
                error_msg = f"❌ Ошибка при отправке: {e}"
                bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text=error_msg)
            
            try:
                os.remove(video_path)
            except:
                pass
        else:
            error_msg = "❌ Не удалось скачать видео. Проверьте ссылку."
            bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text=error_msg)
    else:
        bot.reply_to(message, "Это не похоже на ссылку на Instagram Reel.")

def safe_polling():
    """Безопасный polling с обработкой 409 ошибки"""
    global bot_running
    
    while True:
        try:
            if not bot_running:
                bot_running = True
                logger.info("🔄 Запускаем polling...")
                bot.infinity_polling(timeout=60, long_polling_timeout=60, restart_on_change=True)
                
        except Exception as e:
            bot_running = False
            if "409" in str(e):
                logger.warning("⚠️ Обнаружена 409 ошибка. Останавливаем текущий инстанс...")
                logger.info("🔄 Перезапуск через 15 секунд...")
                time.sleep(15)
            else:
                logger.error(f"❌ Ошибка: {e}")
                logger.info("🔄 Перезапуск через 10 секунд...")
                time.sleep(10)

def start_bot():
    logger.info("🚀 Запускаем бота...")
    
    # Даем время завершиться другим инстансам
    time.sleep(5)
    
    # Запускаем безопасный polling в отдельном потоке
    polling_thread = threading.Thread(target=safe_polling, daemon=True)
    polling_thread.start()
    
    # Главный поток просто ждет
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("⏹️ Останавливаем бота...")
        bot.stop_polling()

if __name__ == '__main__':
    start_bot()
