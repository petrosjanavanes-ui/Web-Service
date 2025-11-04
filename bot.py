import telebot
import os
import requests
import re
import time
import logging
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = '8390506713:AAGKlZcg0IrG99FoNM890tB0W0gNs2tKuvs'
CHANNEL_ID = '@reelsrazyob'

bot = telebot.TeleBot(BOT_TOKEN)

def download_reel(reel_url):
    """Пробуем скачать рилс через доступные методы"""
    try:
        # Метод 1: Пробуем через прямую ссылку Instagram
        result = download_via_direct_instagram(reel_url)
        if result:
            return result
        
        # Метод 2: Пробуем через oEmbed
        result = download_via_oembed(reel_url)
        if result:
            return result
            
        return None
        
    except Exception as e:
        logger.error(f"Общая ошибка: {e}")
        return None

def download_via_direct_instagram(reel_url):
    """Прямой запрос к Instagram"""
    try:
        # Получаем shortcode из URL
        shortcode_match = re.search(r'instagram\.com/reel/([^/?]+)', reel_url)
        if not shortcode_match:
            return None
            
        shortcode = shortcode_match.group(1)
        logger.info(f"Shortcode: {shortcode}")
        
        # Пробуем разные варианты Instagram API
        api_urls = [
            f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=1",
            f"https://www.instagram.com/p/{shortcode}/?__a=1",
            f"https://www.instagram.com/p/{shortcode}/media/?size=l",
        ]
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        for api_url in api_urls:
            try:
                logger.info(f"Пробуем API: {api_url}")
                response = session.get(api_url, timeout=30)
                
                if response.status_code == 200:
                    # Если это JSON ответ
                    if 'application/json' in response.headers.get('content-type', ''):
                        data = response.json()
                        video_url = find_video_in_json(data)
                        if video_url:
                            return download_video_file(video_url, "reel_direct.mp4")
                    
                    # Если это медиа файл
                    elif response.content and len(response.content) > 1000:
                        filename = "reel_media.mp4"
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        if os.path.exists(filename):
                            return filename
                            
            except Exception as e:
                logger.error(f"Ошибка в API {api_url}: {e}")
                continue
                
        return None
        
    except Exception as e:
        logger.error(f"Ошибка direct Instagram: {e}")
        return None

def download_via_oembed(reel_url):
    """Используем официальный oEmbed API Instagram"""
    try:
        oembed_url = "https://www.instagram.com/oembed/"
        params = {
            'url': reel_url,
            'format': 'json'
        }
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        response = session.get(oembed_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"oEmbed данные: {data}")
            
            # oEmbed не дает прямую ссылку на видео, но можем получить HTML
            if 'html' in data:
                html = data['html']
                # Пробуем найти video URL в HTML
                video_match = re.search(r'src="([^"]+\.mp4[^"]*)"', html)
                if video_match:
                    video_url = video_match.group(1)
                    return download_video_file(video_url, "reel_oembed.mp4")
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка oEmbed: {e}")
        return None

def find_video_in_json(data):
    """Ищем видео URL в JSON структуре"""
    try:
        # Рекурсивный поиск в JSON
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ['video_url', 'url', 'src', 'video_versions'] and isinstance(value, str) and '.mp4' in value:
                    return value
                elif isinstance(value, (dict, list)):
                    result = find_video_in_json(value)
                    if result:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = find_video_in_json(item)
                if result:
                    return result
        return None
    except:
        return None

def download_video_file(video_url, filename):
    """Скачивает видео файл"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        logger.info(f"Скачиваем: {video_url}")
        response = session.get(video_url, stream=True, timeout=60)
        
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                logger.info(f"Успешно: {os.path.getsize(filename)} байт")
                return filename
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "📹 Отправьте ссылку на Instagram Reel для публикации в канале.")

@bot.message_handler(func=lambda message: True)
def handle_reel_link(message):
    if 'instagram.com/reel/' in message.text:
        processing_msg = bot.reply_to(message, "🔄 Обрабатываю ссылку...")
        
        try:
            video_path = download_reel(message.text)
            
            if video_path:
                bot.edit_message_text("📤 Отправляю в канал...", 
                                    chat_id=message.chat.id, 
                                    message_id=processing_msg.message_id)
                
                with open(video_path, 'rb') as video:
                    bot.send_video(CHANNEL_ID, video, caption="Новый рилс! 📹")
                
                bot.edit_message_text("✅ Опубликовано в канале!", 
                                    chat_id=message.chat.id, 
                                    message_id=processing_msg.message_id)
                
                # Очистка
                try:
                    os.remove(video_path)
                except:
                    pass
                    
            else:
                bot.edit_message_text("❌ Не удалось обработать ссылку", 
                                    chat_id=message.chat.id, 
                                    message_id=processing_msg.message_id)
                
        except Exception as e:
            bot.edit_message_text(f"❌ Ошибка: {str(e)[:100]}", 
                                chat_id=message.chat.id, 
                                message_id=processing_msg.message_id)
            
    else:
        bot.reply_to(message, "❌ Это не ссылка на Instagram Reel")

def start_bot():
    """Запуск бота"""
    logger.info("🚀 Бот запускается...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=30)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            time.sleep(10)

if __name__ == '__main__':
    start_bot()
