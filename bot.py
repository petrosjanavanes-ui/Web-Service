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
    """Пробуем разные методы скачивания"""
    methods = [
        download_via_ddinstagram,  # Оставляем метод замены ссылки
        download_via_savefrom,
        download_via_insta,
        download_via_tikmate
    ]
    
    for method in methods:
        try:
            logger.info(f"Пробуем метод: {method.__name__}")
            result = method(reel_url)
            if result:
                logger.info(f"Успешно через {method.__name__}")
                return result
        except Exception as e:
            logger.error(f"Метод {method.__name__} не сработал: {e}")
            continue
    
    return None

def download_via_ddinstagram(reel_url):
    """Метод с заменой на ddinstagram - ОСТАВЛЯЕМ!"""
    try:
        # Заменяем домен на ddinstagram
        dd_url = reel_url.replace('www.instagram.com', 'www.ddinstagram.com')
        logger.info(f"Пробуем ddinstagram URL: {dd_url}")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        response = session.get(dd_url, timeout=30)
        response.raise_for_status()
        
        # Ищем видео разными способами
        video_url = None
        
        # Способ 1: Ищем в video тегах
        video_match = re.search(r'<video[^>]*src="([^"]+)"', response.text)
        if video_match:
            video_url = video_match.group(1)
            logger.info(f"Найдено видео через video tag: {video_url}")
        
        # Способ 2: Ищем в JSON данных
        if not video_url:
            json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', response.text)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    video_url = find_video_in_json(data)
                    if video_url:
                        logger.info(f"Найдено видео через JSON: {video_url}")
                except Exception as json_error:
                    logger.error(f"Ошибка парсинга JSON: {json_error}")
        
        # Способ 3: Ищем в og:video
        if not video_url:
            og_match = re.search(r'<meta[^>]*property="og:video"[^>]*content="([^"]+)"', response.text)
            if og_match:
                video_url = og_match.group(1)
                logger.info(f"Найдено видео через og:video: {video_url}")
        
        # Способ 4: Ищем в source тегах
        if not video_url:
            source_match = re.search(r'<source[^>]*src="([^"]+)"[^>]*type="video/mp4"', response.text)
            if source_match:
                video_url = source_match.group(1)
                logger.info(f"Найдено видео через source tag: {video_url}")
        
        if video_url:
            # Исправляем URL если нужно
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            elif video_url.startswith('/'):
                video_url = 'https://www.ddinstagram.com' + video_url
            
            logger.info(f"Финальный URL видео: {video_url}")
            
            # Скачиваем видео
            return download_video_file(video_url, "reel_ddinstagram.mp4")
        
        logger.error("Видео не найдено на странице ddinstagram")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка в ddinstagram методе: {e}")
        return None

def download_via_savefrom(reel_url):
    """Используем savefrom.net API"""
    try:
        # Прямой запрос к savefrom.net
        api_url = "https://api.savefrom.net/api/convert"
        
        payload = {
            "url": reel_url
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Origin': 'https://savefrom.net',
            'Referer': 'https://savefrom.net/',
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Парсим ответ
            url_match = re.search(r'"url":"([^"]+\.mp4[^"]*)"', response.text)
            if url_match:
                video_url = url_match.group(1).replace('\\', '')
                return download_video_file(video_url, "reel_savefrom.mp4")
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка savefrom: {e}")
        return None

def download_via_insta(reel_url):
    """Используем insta.rip"""
    try:
        insta_url = reel_url.replace('www.instagram.com', 'www.insta.rip')
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        response = session.get(insta_url, timeout=30)
        
        # Ищем видео
        video_url = None
        video_match = re.search(r'<video[^>]*src="([^"]+)"', response.text)
        if video_match:
            video_url = video_match.group(1)
        
        if not video_url:
            og_match = re.search(r'<meta[^>]*property="og:video"[^>]*content="([^"]+)"', response.text)
            if og_match:
                video_url = og_match.group(1)
        
        if video_url:
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            return download_video_file(video_url, "reel_insta.mp4")
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка insta.rip: {e}")
        return None

def download_via_tikmate(reel_url):
    """Используем API для TikTok/Instagram"""
    try:
        api_url = "https://api.tikmate.app/api/lookup"
        
        payload = {
            "url": reel_url
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Ищем URL видео в ответе
            video_url = None
            if 'url' in data:
                video_url = data['url']
            elif 'video_url' in data:
                video_url = data['video_url']
            
            if video_url:
                return download_video_file(video_url, "reel_tikmate.mp4")
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка tikmate: {e}")
        return None

def find_video_in_json(data):
    """Рекурсивно ищем видео URL в JSON структуре"""
    try:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and (value.endswith('.mp4') or 'video' in key.lower()):
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'video/mp4,video/webm,video/*;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        logger.info(f"Скачиваем видео с: {video_url}")
        response = session.get(video_url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            file_size = os.path.getsize(filename)
            logger.info(f"Видео успешно скачано: {file_size} байт")
            return filename
        else:
            logger.error("Файл создан но пустой")
            return None
        
    except Exception as e:
        logger.error(f"Ошибка скачивания файла: {e}")
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Бот работает! Отправьте ссылку на Instagram Reel.")

@bot.message_handler(func=lambda message: True)
def handle_reel_link(message):
    if 'instagram.com/reel/' in message.text:
        processing_msg = bot.reply_to(message, "🔄 Скачиваю рилс...")
        
        video_path = download_reel(message.text)
        
        if video_path:
            bot.edit_message_text("📤 Отправляю в канал...", chat_id=message.chat.id, message_id=processing_msg.message_id)
            
            try:
                with open(video_path, 'rb') as video:
                    bot.send_video(CHANNEL_ID, video, caption="Новый рилс! 📹")
                bot.edit_message_text("✅ Рилес опубликован!", chat_id=message.chat.id, message_id=processing_msg.message_id)
            except Exception as e:
                error_msg = f"❌ Ошибка: {str(e)[:100]}"
                bot.edit_message_text(error_msg, chat_id=message.chat.id, message_id=processing_msg.message_id)
            
            try:
                os.remove(video_path)
            except:
                pass
        else:
            bot.edit_message_text("❌ Не удалось скачать видео", chat_id=message.chat.id, message_id=processing_msg.message_id)
    else:
        bot.reply_to(message, "📎 Отправьте ссылку на Instagram Reel")

def start_bot():
    """Запуск бота"""
    while True:
        try:
            logger.info("🚀 Запускаем бота...")
            bot.polling(none_stop=True, timeout=30)
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            logger.info("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == '__main__':
    logger.info("🤖 Инициализация бота...")
    start_bot()
