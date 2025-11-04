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
    """Скачиваем рилс через работающий сервис"""
    try:
        logger.info(f"Скачиваем: {reel_url}")
        
        # Метод 1: Используем SnapInsta.io API
        result = download_via_snapinsta(reel_url)
        if result:
            return result
            
        # Метод 2: Используем прямую ссылку Instagram
        result = download_via_direct(reel_url)
        if result:
            return result
            
        return None
        
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None

def download_via_snapinsta(reel_url):
    """Используем SnapInsta.io - работает надежно"""
    try:
        # Получаем shortcode из URL
        shortcode_match = re.search(r'instagram\.com/reel/([^/?]+)', reel_url)
        if not shortcode_match:
            return None
            
        shortcode = shortcode_match.group(1)
        
        # SnapInsta API
        api_url = f"https://snapinsta.io/api/ajaxSearch"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://snapinsta.io',
            'Referer': 'https://snapinsta.io/',
        }
        
        data = {
            'q': f'https://www.instagram.com/reel/{shortcode}/',
            't': 'media',
            'lang': 'en'
        }
        
        session = requests.Session()
        response = session.post(api_url, data=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result_data = response.json()
            logger.info(f"SnapInsta ответ: {result_data}")
            
            # Ищем ссылку на видео в ответе
            if 'data' in result_data:
                video_url = find_video_url_in_response(result_data['data'])
                if video_url:
                    return download_video_file(video_url, f"reel_{shortcode}.mp4")
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка SnapInsta: {e}")
        return None

def download_via_direct(reel_url):
    """Прямое скачивание через Instagram"""
    try:
        shortcode_match = re.search(r'instagram\.com/reel/([^/?]+)', reel_url)
        if not shortcode_match:
            return None
            
        shortcode = shortcode_match.group(1)
        
        # Пробуем разные варианты Instagram API
        api_urls = [
            f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=1",
            f"https://www.instagram.com/p/{shortcode}/?__a=1",
        ]
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
        })
        
        for api_url in api_urls:
            try:
                logger.info(f"Пробуем API: {api_url}")
                response = session.get(api_url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    video_url = find_video_in_instagram_json(data)
                    if video_url:
                        return download_video_file(video_url, f"reel_direct_{shortcode}.mp4")
                        
            except Exception as e:
                logger.error(f"Ошибка в API {api_url}: {e}")
                continue
                
        return None
        
    except Exception as e:
        logger.error(f"Ошибка прямого скачивания: {e}")
        return None

def find_video_url_in_response(html_content):
    """Ищем URL видео в HTML ответе"""
    try:
        # Ищем в JSON данных
        json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', html_content)
        if json_match:
            data = json.loads(json_match.group(1))
            video_url = find_video_in_instagram_json(data)
            if video_url:
                return video_url
        
        # Ищем прямые ссылки на видео
        video_patterns = [
            r'"video_url":"([^"]+)"',
            r'src="([^"]+\.mp4[^"]*)"',
            r'content="([^"]+\.mp4[^"]*)"',
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if '.mp4' in match and 'blob:' not in match:
                    video_url = match.replace('\\u0026', '&')
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    return video_url
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка поиска видео: {e}")
        return None

def find_video_in_instagram_json(data):
    """Ищем видео в JSON структуре Instagram"""
    try:
        # Рекурсивный поиск URL видео
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.endswith('.mp4') and 'video' in key.lower():
                    return value
                elif isinstance(value, (dict, list)):
                    result = find_video_in_instagram_json(value)
                    if result:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = find_video_in_instagram_json(item)
                if result:
                    return result
        return None
    except:
        return None

def download_video_file(video_url, filename):
    """Скачивает видео файл с проверкой размера"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'video/mp4,video/*;q=0.9,*/*;q=0.8',
        })
        
        logger.info(f"Скачиваем видео: {video_url}")
        response = session.get(video_url, stream=True, timeout=60)
        
        if response.status_code == 200:
            total_size = 0
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            # Проверяем размер файла
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                logger.info(f"Размер файла: {file_size} байт")
                
                # Видео должно быть больше 100KB
                if file_size > 100 * 1024:
                    logger.info(f"✅ Видео успешно скачано: {file_size} байт")
                    return filename
                else:
                    logger.error(f"❌ Файл слишком маленький: {file_size} байт")
                    os.remove(filename)
                    return None
            else:
                logger.error("❌ Файл не создан")
                return None
        else:
            logger.error(f"❌ Ошибка HTTP: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания файла: {e}")
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Бот работает! Отправьте ссылку на Instagram Reel для публикации в канале.")

@bot.message_handler(func=lambda message: True)
def handle_reel_link(message):
    if 'instagram.com/reel/' in message.text:
        processing_msg = bot.reply_to(message, "🔄 Скачиваю рилс...")
        
        try:
            video_path = download_reel(message.text)
            
            if video_path and os.path.exists(video_path):
                file_size = os.path.getsize(video_path)
                logger.info(f"Файл готов: {file_size} байт")
                
                bot.edit_message_text("📤 Отправляю в канал...", 
                                    chat_id=message.chat.id, 
                                    message_id=processing_msg.message_id)
                
                try:
                    with open(video_path, 'rb') as video:
                        bot.send_video(CHANNEL_ID, video, caption="Новый рилс! 📹")
                    
                    bot.edit_message_text("✅ Рилес успешно опубликован!", 
                                        chat_id=message.chat.id, 
                                        message_id=processing_msg.message_id)
                    
                except Exception as e:
                    error_msg = f"❌ Ошибка отправки: {str(e)[:100]}"
                    bot.edit_message_text(error_msg, 
                                        chat_id=message.chat.id, 
                                        message_id=processing_msg.message_id)
                
                # Очистка
                try:
                    os.remove(video_path)
                except:
                    pass
                    
            else:
                bot.edit_message_text("❌ Не удалось скачать видео", 
                                    chat_id=message.chat.id, 
                                    message_id=processing_msg.message_id)
                
        except Exception as e:
            logger.error(f"Общая ошибка: {e}")
            bot.edit_message_text("❌ Произошла ошибка при обработке", 
                                chat_id=message.chat.id, 
                                message_id=processing_msg.message_id)
            
    else:
        bot.reply_to(message, "📎 Отправьте ссылку на Instagram Reel")

def safe_polling():
    """Безопасный запуск бота"""
    while True:
        try:
            logger.info("🚀 Запускаем бота...")
            bot.polling(none_stop=True, timeout=30, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            if "409" in str(e):
                logger.warning("⚠️ 409 ошибка, ждем 30 секунд...")
                time.sleep(30)
            else:
                time.sleep(10)

if __name__ == '__main__':
    logger.info("🤖 Инициализация бота...")
    time.sleep(10)  # Даем время на завершение старых процессов
    safe_polling()
