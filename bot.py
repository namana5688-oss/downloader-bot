import telebot
import yt_dlp
import os
import tempfile
from pathlib import Path
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8764355663:AAGe2uMmOBPCEqsPTFzlr6PJoALQEuLzEps"
MAX_FILE_MB = 50
BOT_ID = "@thebestdownloader_bot"

bot = telebot.TeleBot(BOT_TOKEN)
user_requests = {}

def format_size(b):
    return f"{b/(1024*1024):.1f} MB"

def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
        },
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

def download_video(url, quality, tmpdir):
    if quality == 'audio_128':
        fmt = 'bestaudio/best'
        postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}]
    elif quality == 'audio_320':
        fmt = 'bestaudio/best'
        postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
    elif quality == '144':
        fmt = 'best[height<=144]/worst'
        postprocessors = []
    elif quality == '240':
        fmt = 'best[height<=240]/best[height<=360]'
        postprocessors = []
    elif quality == '360':
        fmt = 'best[height<=360]'
        postprocessors = []
    elif quality == '480':
        fmt = 'best[height<=480]'
        postprocessors = []
    elif quality == '720':
        fmt = 'best[height<=720][filesize<45M]/best[height<=720]'
        postprocessors = []
    elif quality == '1080':
        fmt = 'best[height<=1080][filesize<45M]/best[height<=1080]'
        postprocessors = []
    else:
        fmt = 'best[filesize<45M]/best'
        postprocessors = []

    ydl_opts = {
        'outtmpl': os.path.join(tmpdir, '%(title).50s.%(ext)s'),
        'format': fmt,
        'quiet': True,
        'noplaylist': True,
        'max_filesize': 45 * 1024 * 1024,
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
        },
    }
    if postprocessors:
        ydl_opts['postprocessors'] = postprocessors

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    files = list(Path(tmpdir).iterdir())
    return str(files[0]) if files else None

def download_thumbnail(url, tmpdir):
    try:
        import requests
        r = requests.get(url, timeout=10)
        thumb_path = os.path.join(tmpdir, 'thumb.jpg')
        with open(thumb_path, 'wb') as f:
            f.write(r.content)
        return thumb_path
    except:
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
        "👋 سلام! به *Best Downloader Bot* خوش اومدی!\n\n"
        "📥 لینک ویدیو یا عکست رو بفرست تا دانلودش کنم.\n\n"
        "پشتیبانی از:\n"
        "▸ YouTube\n▸ Instagram\n▸ TikTok\n"
        "▸ Pinterest\n▸ Twitter/X\n▸ و ۱۰۰۰+ سایت دیگه!\n\n"
        f"🆔 {BOT_ID}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        "ℹ️ *طرز استفاده:*\n\n"
        "۱. لینک رو بفرست\n"
        "۲. کیفیت دلخواه رو انتخاب کن\n"
        "۳. صبر کن دانلود بشه\n"
        "۴. فایلت رو دریافت کن!\n\n"
        "⚠️ حداکثر حجم فایل: ۵۰ مگابایت",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text and m.text.startswith('http'))
def handle_link(message):
    url = message.text.strip()
    status = bot.reply_to(message, "🔍 در حال دریافت اطلاعات...")

    try:
        info = get_video_info(url)
        title = info.get('title', 'ویدیو')
        description = info.get('description', '')

        desc_short = description[:300] + "..." if len(description) > 300 else description

        user_requests[message.chat.id] = {
            'url': url,
            'title': title,
            'description': desc_short,
            'thumbnail': info.get('thumbnail', None)
        }

        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🎵 MP3 128k", callback_data=f"dl_audio_128_{message.chat.id}"),
            InlineKeyboardButton("🎵 MP3 320k", callback_data=f"dl_audio_320_{message.chat.id}")
        )
        markup.row(
            InlineKeyboardButton("📱 144p", callback_data=f"dl_144_{message.chat.id}"),
            InlineKeyboardButton("📱 240p", callback_data=f"dl_240_{message.chat.id}"),
            InlineKeyboardButton("📱 360p", callback_data=f"dl_360_{message.chat.id}")
        )
        markup.row(
            InlineKeyboardButton("🖥 480p", callback_data=f"dl_480_{message.chat.id}"),
            InlineKeyboardButton("🖥 720p", callback_data=f"dl_720_{message.chat.id}"),
            InlineKeyboardButton("🎯 1080p", callback_data=f"dl_1080_{message.chat.id}")
        )

        bot.edit_message_text(
            f"🎬 *{title}*\n\nکیفیت مورد نظر رو انتخاب کن:",
            message.chat.id,
            status.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )

    except Exception as e:
        bot.edit_message_text("❌ خطا در دریافت اطلاعات. لینک ممکنه خصوصی یا محدود باشه.", message.chat.id, status.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def handle_download(call):
    parts = call.data.split('_')
    
    if parts[1] == 'audio':
        quality = f"audio_{parts[2]}"
        chat_id = int(parts[3])
    else:
        quality = parts[1]
        chat_id = int(parts[2])

    data = user_requests.get(chat_id)
    if not data:
        bot.answer_callback_query(call.id, "لینک پیدا نشد!")
        return

    url = data['url']
    title = data['title']
    description = data['description']
    thumbnail_url = data['thumbnail']

    bot.answer_callback_query(call.id, "در حال دانلود...")
    bot.edit_message_text("⏳ در حال دانلود... صبر کن.", chat_id, call.message.message_id)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = download_video(url, quality, tmpdir)

            if not file_path:
                bot.edit_message_text("❌ دانلود ناموفق بود.", chat_id, call.message.message_id)
                return

            file_size = os.path.getsize(file_path)
            ext = Path(file_path).suffix.lower()

            if file_size > MAX_FILE_MB * 1024 * 1024:
                bot.edit_message_text(f"❌ فایل خیلی بزرگه ({format_size(file_size)}). حداکثر ۵۰MB.", chat_id, call.message.message_id)
                return

            bot.edit_message_text(f"📤 در حال آپلود ({format_size(file_size)})...", chat_id, call.message.message_id)

            # Caption with title and bot ID
            caption = f"{title}\n\n🆔 {BOT_ID}"

            # Download thumbnail
            thumb_path = None
            if thumbnail_url:
                thumb_path = download_thumbnail(thumbnail_url, tmpdir)

            with open(file_path, 'rb') as f:
                if 'audio' in quality or ext in ['.mp3', '.m4a', '.ogg']:
                    bot.send_audio(chat_id, f, caption=caption)
                elif ext in ['.mp4', '.mkv', '.webm', '.mov']:
                    thumb_file = open(thumb_path, 'rb') if thumb_path else None
                    bot.send_video(
                        chat_id, f,
                        caption=caption,
                        thumb=thumb_file,
                        supports_streaming=True
                    )
                    if thumb_file:
                        thumb_file.close()
                elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    bot.send_photo(chat_id, f, caption=caption)
                else:
                    bot.send_document(chat_id, f, caption=caption)

            bot.delete_message(chat_id, call.message.message_id)

    except Exception as e:
        bot.edit_message_text("❌ خطا در دانلود. لینک ممکنه خصوصی یا محدود باشه.", chat_id, call.message.message_id)

@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.reply_to(message, "⚠️ لطفاً یه لینک معتبر بفرست!")

print("ربات شروع به کار کرد...")
bot.polling(none_stop=True)
