import telebot
import os
import requests
import re
import time
import logging
from urllib.parse import urlparse

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = '8390506713:AAGKlZcg0IrG99FoNM890tB0W0gNs2tKuvs'
CHANNEL_ID = '@reelsrazyob'

bot = telebot.TeleBot(BOT_TOKEN)

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
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
        })
        
        # Получаем страницу ddinstagram
        response = session.get(ddinstagram_url, timeout=30)
        response.raise_for_status()
        
        # Ищем видео в нескольких возможных местах
        video_url = None
        
        # Способ 1: Ищем <video> тег
        video_match = re.search(r'<video[^>]*src="([^"]+)"', response.text)
        if video_match:
            video_url = video_match.group(1)
            logger.info(f"Найдено видео через video tag: {video_url}")
        
        # Способ 2: Ищем в JSON данных
        if not video_url:
            json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', response.text)
            if json_match:
                import json
                try:
                    data = json.loads(json_match.group(1))
                    # Пытаемся извлечь URL видео из структуры данных Instagram
                    video_url = extract_video_from_json(data)
                    if video_url:
                        logger.info(f"Найдено видео через JSON: {video_url}")
                except:
                    pass
        
        # Способ 3: Ищем в og:video meta tag
        if not video_url:
            og_match = re.search(r'<meta[^>]*property="og:video"[^>]*content="([^"]+)"', response.text)
            if og_match:
                video_url = og_match.group(1)
                logger.info(f"Найдено видео через og:video: {video_url}")
        
        if video_url:
            # Если URL относительный, делаем его абсолютным
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            elif video_url.startswith('/'):
                video_url = 'https://www.ddinstagram.com' + video_url
            
            # Скачиваем видео
            video_response = session.get(video_url, stream=True, timeout=60)
            video_response.raise_for_status()
            
            filename = "reel_video_ddinstagram.mp4"
            with open(filename, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                logger.info(f"Видео успешно скачано через ddinstagram, размер: {os.path.getsize(filename)} байт")
                return filename
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка в ddinstagram методе: {e}")
        return None

def extract_video_from_json(data):
    """Пытаемся извлечь URL видео из JSON структуры Instagram"""
    try:
        # Пробуем разные пути в JSON структуре
        paths_to_try = [
            ['entry_data', 'PostPage', 0, 'graphql', 'shortcode_media', 'video_url'],
            ['graphql', 'shortcode_media', 'video_url'],
            ['video_url'],
            ['items', 0, 'video_versions', 0, 'url'],
        ]
        
        for path in paths_to_try:
            try:
                result = data
                for key in path:
                    if isinstance(key, int) and isinstance(result, list):
                        result = result[key]
                    else:
                        result = result[key]
                if result and 'video' in result:
                    return result
            except:
                continue
        return None
    except:
        return None

def download_via_ssstik(reel_url):
    """Скачивание через ssstik.io"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        })
        
        # Получаем главную страницу для токена
        ssstik_url = "https://ssstik.io"
        response = session.get(ssstik_url, timeout=30)
        response.raise_for_status()
        
        # Ищем токен
        token_match = re.search(r'name="tt" value="([^"]+)"', response.text)
        if not token_match:
            logger.error("Не удалось найти токен на ssstik.io")
            return None
        
        token = token_match.group(1)
        logger.info(f"Получен токен ssstik: {token}")
        
        # Отправляем запрос на скачивание
        download_url = "https://ssstik.io/abc?url=dl"
        data = {
            "id": reel_url,
            "locale": "en",
            "tt": token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://ssstik.io',
            'Referer': 'https://ssstik.io/',
        }
        
        response = session.post(download_url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Ищем ссылку на видео
        video_url_match = re.search(r'href="(https[^"]+\.mp4[^"]*)"', response.text)
        if not video_url_match:
            logger.error("Не удалось найти ссылку на видео в ответе ssstik")
            return None
        
        video_url = video_url_match.group(1)
        logger.info(f"Найдена ссылка на видео: {video_url}")
        
        # Скачиваем видео
        video_response = session.get(video_url, stream=True, timeout=60)
        video_response.raise_for_status()
        
        filename = "reel_video_ssstik.mp4"
        with open(filename, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            logger.info(f"Видео успешно скачано через ssstik, размер: {os.path.getsize(filename)} байт")
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
        
        # Получаем главную страницу
        snaptik_url = "https://snaptik.app"
        response = session.get(snaptik_url, timeout=30)
        response.raise_for_status()
        
        # Ищем токен
        token_match = re.search(r'name="token" value="([^"]+)"', response.text)
        if not token_match:
            logger.error("Не удалось найти токен на snaptik.app")
            return None
        
        token = token_match.group(1)
        logger.info(f"Получен токен snaptik: {token}")
        
        # Отправляем запрос
        api_url = "https://snaptik.app/abc2.php"
        data = {
            "url": reel_url,
            "token": token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://snaptik.app',
            'Referer': 'https://snaptik.app/',
        }
        
        response = session.post(api_url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Парсим ответ
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
                logger.info(f"Видео успешно скачано через snaptik, размер: {os.path.getsize(filename)} байт")
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
            file_size = os.path.getsize(video_path)
            logger.info(f"Файл готов к отправке, размер: {file_size} байт")
            
            bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text="📤 Отправляю в канал...")
            
            try:
                with open(video_path, 'rb') as video:
                    bot.send_video(CHANNEL_ID, video, caption="Новый рилс! 📹")
                bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text="✅ Рилес успешно опубликован в канале!")
            except Exception as e:
                error_msg = f"❌ Ошибка при отправке: {e}"
                logger.error(error_msg)
                bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text=error_msg)
            
            # Удаляем временный файл
            try:
                os.remove(video_path)
                logger.info("Временный файл удален")
            except:
                pass
        else:
            error_msg = "❌ Не удалось скачать видео. Проверьте ссылку или попробуйте позже."
            logger.error(error_msg)
            bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text=error_msg)
    else:
        bot.reply_to(message, "Это не похоже на ссылку на Instagram Reel. Отправьте ссылку вида: https://www.instagram.com/reel/...")

def start_bot():
    logger.info("🚀 Запускаем бота...")
    while True:
        try:
            logger.info("🤖 Бот запущен и слушает сообщения...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            logger.info("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == '__main__':
    start_bot()
