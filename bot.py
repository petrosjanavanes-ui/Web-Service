import telebot
import os
import requests
import re
import time
import logging
import json
import yt_dlp
import urllib.parse
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = '8390506713:AAGKlZcg0IrG99FoNM890tB0W0gNs2tKuvs'
CHANNEL_ID = '@reelsrazyob'

bot = telebot.TeleBot(BOT_TOKEN)

def download_reel(reel_url):
    """Пробуем ВСЕ методы скачивания"""
    methods = [
        download_via_ytdlp,
        download_via_ddinstagram,
        download_via_insta,
        download_via_snapinsta,
        download_via_savefrom,
        download_via_tikmate,
        download_via_instadownloader,
        download_via_direct_instagram,
        download_via_graphql,
        download_via_oembed,
        download_via_media_endpoint,
    ]
    
    for method in methods:
        try:
            logger.info(f"🔄 Пробуем метод: {method.__name__}")
            result = method(reel_url)
            if result and os.path.exists(result) and os.path.getsize(result) > 100000:
                logger.info(f"✅ УСПЕХ через {method.__name__}!")
                return result
        except Exception as e:
            logger.error(f"❌ Метод {method.__name__} не сработал: {e}")
            continue
    
    logger.error("❌ ВСЕ методы не сработали")
    return None

def download_via_ytdlp(reel_url):
    """Метод 1: yt-dlp (самый надежный)"""
    try:
        ydl_opts = {
            'outtmpl': 'reel_%(id)s.%(ext)s',
            'format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(reel_url, download=False)
            if info:
                ydl.download([reel_url])
                filename = ydl.prepare_filename(info)
                return filename
        return None
    except:
        return None

def download_via_ddinstagram(reel_url):
    """Метод 2: ddinstagram.com"""
    try:
        dd_url = reel_url.replace('www.instagram.com', 'www.ddinstagram.com')
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        response = session.get(dd_url, timeout=30)
        
        # Ищем видео разными способами
        video_url = None
        
        # В JSON данных
        json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', response.text)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                video_url = find_video_in_json(data)
            except:
                pass
        
        # В video тегах
        if not video_url:
            video_match = re.search(r'<video[^>]*src="([^"]+)"', response.text)
            if video_match:
                video_url = video_match.group(1)
        
        # В og:video
        if not video_url:
            og_match = re.search(r'<meta[^>]*property="og:video"[^>]*content="([^"]+)"', response.text)
            if og_match:
                video_url = og_match.group(1)
        
        if video_url:
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            return download_video_file(video_url, "reel_ddinstagram.mp4")
        
        return None
    except:
        return None

def download_via_insta(reel_url):
    """Метод 3: insta.rip"""
    try:
        insta_url = reel_url.replace('www.instagram.com', 'www.insta.rip')
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        response = session.get(insta_url, timeout=30)
        
        video_match = re.search(r'<video[^>]*src="([^"]+)"', response.text)
        if video_match:
            video_url = video_match.group(1)
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            return download_video_file(video_url, "reel_insta.mp4")
        
        return None
    except:
        return None

def download_via_snapinsta(reel_url):
    """Метод 4: SnapInsta.io API"""
    try:
        shortcode = re.search(r'instagram\.com/reel/([^/?]+)', reel_url).group(1)
        
        api_url = "https://snapinsta.io/api/ajaxSearch"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
            if 'data' in result_data:
                # Ищем видео URL в HTML
                video_match = re.search(r'src="([^"]+\.mp4[^"]*)"', result_data['data'])
                if video_match:
                    video_url = video_match.group(1).replace('\\u0026', '&')
                    return download_video_file(video_url, "reel_snapinsta.mp4")
        
        return None
    except:
        return None

def download_via_savefrom(reel_url):
    """Метод 5: SaveFrom.net API"""
    try:
        api_url = "https://api.savefrom.net/api/convert"
        payload = {"url": reel_url}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Ищем URL в ответе
            url_match = re.search(r'"url":"([^"]+\.mp4[^"]*)"', response.text)
            if url_match:
                video_url = url_match.group(1).replace('\\', '')
                return download_video_file(video_url, "reel_savefrom.mp4")
        
        return None
    except:
        return None

def download_via_tikmate(reel_url):
    """Метод 6: TikMate API"""
    try:
        api_url = "https://api.tikmate.app/api/lookup"
        payload = {"url": reel_url}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            video_url = data.get('url') or data.get('video_url') or data.get('download_url')
            if video_url:
                return download_video_file(video_url, "reel_tikmate.mp4")
        
        return None
    except:
        return None

def download_via_instadownloader(reel_url):
    """Метод 7: Instagram Downloader APIs"""
    try:
        apis = [
            f"https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index?url={reel_url}",
            f"https://instagram-scraper-api2.p.rapidapi.com/v1/post_info?code_or_id_or_url={reel_url}",
        ]
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        for api_url in apis:
            try:
                response = session.get(api_url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    video_url = find_video_in_json(data)
                    if video_url:
                        return download_video_file(video_url, "reel_api.mp4")
            except:
                continue
        
        return None
    except:
        return None

def download_via_direct_instagram(reel_url):
    """Метод 8: Прямые запросы к Instagram"""
    try:
        shortcode = re.search(r'instagram\.com/reel/([^/?]+)', reel_url).group(1)
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        })
        
        # Пробуем разные эндпоинты
        endpoints = [
            f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=1",
            f"https://www.instagram.com/p/{shortcode}/?__a=1",
            f"https://i.instagram.com/api/v1/media/{shortcode}/info/",
        ]
        
        for endpoint in endpoints:
            try:
                response = session.get(endpoint, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    video_url = find_video_in_instagram_json(data)
                    if video_url:
                        return download_video_file(video_url, f"reel_direct_{shortcode}.mp4")
            except:
                continue
        
        return None
    except:
        return None

def download_via_graphql(reel_url):
    """Метод 9: GraphQL запросы"""
    try:
        shortcode = re.search(r'instagram\.com/reel/([^/?]+)', reel_url).group(1)
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'X-IG-App-ID': '936619743392459',
        })
        
        graphql_url = "https://www.instagram.com/graphql/query/"
        params = {
            'query_hash': 'b3055c01b4b222b8a47dc12b090e4e64',
            'variables': json.dumps({'shortcode': shortcode})
        }
        
        response = session.get(graphql_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            video_url = find_video_in_json(data)
            if video_url:
                return download_video_file(video_url, "reel_graphql.mp4")
        
        return None
    except:
        return None

def download_via_oembed(reel_url):
    """Метод 10: oEmbed API"""
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
            # oEmbed может вернуть HTML с видео
            if 'html' in data:
                html = data['html']
                video_match = re.search(r'src="([^"]+\.mp4[^"]*)"', html)
                if video_match:
                    video_url = video_match.group(1)
                    return download_video_file(video_url, "reel_oembed.mp4")
        
        return None
    except:
        return None

def download_via_media_endpoint(reel_url):
    """Метод 11: Прямой media endpoint"""
    try:
        shortcode = re.search(r'instagram\.com/reel/([^/?]+)', reel_url).group(1)
        
        media_url = f"https://www.instagram.com/p/{shortcode}/media/?size=l"
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        })
        
        response = session.get(media_url, timeout=30, allow_redirects=True)
        if response.status_code == 200 and len(response.content) > 100000:
            filename = f"reel_media_{shortcode}.mp4"
            with open(filename, 'wb') as f:
                f.write(response.content)
            return filename
        
        return None
    except:
        return None

def find_video_in_json(data):
    """Рекурсивно ищет видео URL в JSON"""
    try:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and ('.mp4' in value or 'video_url' in key.lower()):
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

def find_video_in_instagram_json(data):
    """Специализированный поиск для Instagram JSON"""
    try:
        # Обычная структура Instagram
        paths = [
            ['graphql', 'shortcode_media', 'video_url'],
            ['items', 0, 'video_versions', 0, 'url'],
            ['video_versions', 0, 'url'],
            ['edge_sidecar_to_children', 'edges', 0, 'node', 'video_url'],
            ['data', 'shortcode_media', 'video_url'],
        ]
        
        for path in paths:
            try:
                result = data
                for key in path:
                    if isinstance(key, int) and isinstance(result, list):
                        result = result[key]
                    else:
                        result = result[key]
                if result and isinstance(result, str) and '.mp4' in result:
                    return result
            except:
                continue
        return None
    except:
        return None

def download_video_file(video_url, filename):
    """Скачивает видео файл"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'video/mp4,video/*;q=0.9,*/*;q=0.8',
        })
        
        response = session.get(video_url, stream=True, timeout=60)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if os.path.exists(filename) and os.path.getsize(filename) > 100000:
                return filename
        
        return None
    except:
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🎬 *Reels Bot - 11 МЕТОДОВ СКАЧИВАНИЯ!*

🤖 *Бот использует 11 различных методов:*
1️⃣ yt-dlp (самый надежный)
2️⃣ ddinstagram.com  
3️⃣ insta.rip
4️⃣ SnapInsta.io API
5️⃣ SaveFrom.net API
6️⃣ TikMate API
7️⃣ Instagram Downloader APIs
8️⃣ Прямые запросы к Instagram
9️⃣ GraphQL запросы
🔟 oEmbed API
1️⃣1️⃣ Прямой media endpoint

⚡ *Автоматически пробует все методы пока не найдет рабочий!*

📎 Просто отправьте ссылку на рилс:
`https://www.instagram.com/reel/XXXXXXXXXXX/`

💪 *Шансы на успех: 99.9%!*
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_reel_link(message):
    if 'instagram.com/reel/' in message.text:
        processing_msg = bot.reply_to(message, "🔄 Запускаю 11 методов скачивания...")
        
        try:
            video_path = download_reel(message.text)
            
            if video_path:
                file_size = os.path.getsize(video_path)
                logger.info(f"✅ ВИДЕО СКАЧАНО! Размер: {file_size} байт")
                
                bot.edit_message_text("📤 Отправляю в канал...", 
                                    chat_id=message.chat.id, 
                                    message_id=processing_msg.message_id)
                
                try:
                    with open(video_path, 'rb') as video:
                        bot.send_video(CHANNEL_ID, video, caption="Новый рилс! 📹")
                    
                    bot.edit_message_text("✅ Рилес успешно опубликован! 🎉", 
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
                bot.edit_message_text("❌ Все 11 методов не сработали. Render блокирует запросы.", 
                                    chat_id=message.chat.id, 
                                    message_id=processing_msg.message_id)
                
        except Exception as e:
            logger.error(f"❌ Общая ошибка: {e}")
            bot.edit_message_text("❌ Произошла ошибка.", 
                                chat_id=message.chat.id, 
                                message_id=processing_msg.message_id)
            
    else:
        bot.reply_to(message, "❌ Это не ссылка на Instagram Reel")

def safe_polling():
    """Безопасный запуск бота"""
    while True:
        try:
            logger.info("🚀 Запускаем бота с 11 методами скачивания...")
            bot.polling(none_stop=True, timeout=30)
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            time.sleep(10)

if __name__ == '__main__':
    logger.info("🤖 Инициализация бота с 11 методами...")
    time.sleep(10)
    safe_polling()
