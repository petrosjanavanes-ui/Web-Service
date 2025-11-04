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
    try:
        logger.info(f"Пытаемся скачать рилс: {reel_url}")
        # Пробуем сначала ssstik.io
        result = download_via_ssstik(reel_url)
        if result:
            logger.info("Успешно скачано через ssstik.io")
            return result
        else:
            # Если не сработало, пробуем snaptik.app
            logger.info("ssstik.io не сработал, пробуем snaptik.app...")
            result = download_via_snaptik(reel_url)
            if result:
                logger.info("Успешно скачано через snaptik.app")
                return result
            else:
                logger.error("Оба метода не сработали")
                return None
    except Exception as e:
        logger.error(f"Общая ошибка при скачивании: {e}")
        return None

def download_via_ssstik(reel_url):
    """Скачивание через ssstik.io"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
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
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        response = session.post(download_url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Ищем ссылку на видео несколькими способами
        video_url = None
        
        # Способ 1: Ищем в href
        video_url_match = re.search(r'href="(https[^"]+\.mp4[^"]*)"', response.text)
        if video_url_match:
            video_url = video_url_match.group(1)
        else:
            # Способ 2: Ищем в data-видео
            video_url_match = re.search(r'data-video="(https[^"]+)"', response.text)
            if video_url_match:
                video_url = video_url_match.group(1)
        
        if not video_url:
            logger.error("Не удалось найти ссылку на видео в ответе ssstik")
            return None
        
        logger.info(f"Найдена ссылка на видео: {video_url}")
        
        # Скачиваем видео
        video_response = session.get(video_url, stream=True, timeout=60)
        video_response.raise_for_status()
        
        filename = "reel_video.mp4"
        with open(filename, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Проверяем что файл создан и не пустой
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            logger.info(f"Видео успешно скачано, размер: {os.path.getsize(filename)} байт")
            return filename
        else:
            logger.error("Файл не создан или пустой")
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
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
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
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        response = session.post(api_url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Парсим JSON ответ
        import json
        try:
            data = response.json()
            if data.get('status') == 'success' and data.get('data', {}).get('url'):
                video_url = data['data']['url']
                
                # Скачиваем видео
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
                    
        except json.JSONDecodeError:
            # Пробуем найти ссылку в HTML
            video_url_match = re.search(r'"download_url":"([^"]+)"', response.text)
            if video_url_match:
                video_url = video_url_match.group(1).replace('\\', '')
                
                video_response = session.get(video_url, stream=True, timeout=60)
                video_response.raise_for_status()
                
                filename = "reel_video_snaptik2.mp4"
                with open(filename, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                if os.path.exists(filename) and os.path.getsize(filename) > 0:
                    logger.info(f"Видео успешно скачано через snaptik (метод 2), размер: {os.path.getsize(filename)} байт")
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
