import telebot
import yt_dlp
import os
import tempfile
import requests
from pathlib import Path
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8764355663:AAGe2uMmOBPCEqsPTFzlr6PJoALQEuLzEps"
MAX_FILE_MB = 50

bot = telebot.TeleBot(BOT_TOKEN)

# Store user requests temporarily
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
    if quality == 'audio':
        fmt = 'bestaudio/best'
    elif quality == '360':
        fmt = 'best[height<=360][filesize<45M]/best[height<=360]'
    elif quality == '720':
        fmt = 'best[height<=720][filesize<45M]/best[height<=720]'
    elif quality == '1080':
        fmt = 'best[height<=1080][filesize<45M]/best[height<=1080]'
    else:
        fmt = 'best[filesize<45M]/best'

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

    if quality == 'audio':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    files = list(Path(tmpdir).iterdir())
    return str(files[0]) if files else None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
        "👋 سلام! به *Best Downloader Bot* خوش اومدی!\n\n"
        "📥 لینک ویدیو یا عکست رو بفرست تا دانلودش کنم.\n\n"
        "پشتیبانی از:\n"
        "▸ YouTube\n▸ Instagram\n▸ TikTok\n"
        "▸ Pinterest\n▸ Twitter/X\n▸ و ۱۰۰۰+ سایت دیگه!",
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
        thumbnail = info.get('thumbnail', None)
        duration = info.get('duration', 0)
        uploader = info.get('uploader', '')

        if duration:
            mins = duration // 60
            secs = duration % 60
            dur_text = f"⏱ {mins}:{secs:02d}"
        else:
            dur_text = ""

        desc_short = description[:200] + "..." if len(description) > 200 else description

        caption = f"🎬 *{title}*\n"
        if uploader:
            caption += f"👤 {uploader}\n"
        if dur_text:
            caption += f"{dur_text}\n"
        if desc_short:
            caption += f"\n📝 {desc_short}"

        # Store request
        user_requests[message.chat.id] = url

        # Quality keyboard
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🎵 فقط صدا (MP3)", callback_data=f"dl_audio_{message.chat.id}")
        )
        markup.row(
            InlineKeyboardButton("📱 360p", callback_data=f"dl_360_{message.chat.id}"),
            InlineKeyboardButton("🖥 720p", callback_data=f"dl_720_{message.chat.id}")
        )
        markup.row(
            InlineKeyboardButton("🎯 1080p", callback_data=f"dl_1080_{message.chat.id}")
        )

        bot.delete_message(message.chat.id, status.message_id)

        # Send thumbnail with info
        if thumbnail:
            try:
                bot.send_photo(
                    message.chat.id,
                    thumbnail,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    message.chat.id,
                    caption,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
        else:
            bot.send_message(
                message.chat.id,
                caption,
                parse_mode="Markdown",
                reply_markup=markup
            )

    except Exception as e:
        bot.edit_message_text("❌ خطا در دریافت اطلاعات. لینک ممکنه خصوصی یا محدود باشه.", message.chat.id, status.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def handle_download(call):
    parts = call.data.split('_')
    quality = parts[1]
    chat_id = int(parts[2])

    url = user_requests.get(chat_id)
    if not url:
        bot.answer_callback_query(call.id, "لینک پیدا نشد!")
        return

    bot.answer_callback_query(call.id, "در حال دانلود...")
    status = bot.send_message(chat_id, "⏳ در حال دانلود... صبر کن.")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = download_video(url, quality, tmpdir)

            if not file_path:
                bot.edit_message_text("❌ دانلود ناموفق بود.", chat_id, status.message_id)
                return

            file_size = os.path.getsize(file_path)
            ext = Path(file_path).suffix.lower()

            if file_size > MAX_FILE_MB * 1024 * 1024:
                bot.edit_message_text(f"❌ فایل خیلی بزرگه ({format_size(file_size)}). حداکثر ۵۰MB.", chat_id, status.message_id)
                return

            bot.edit_message_text(f"📤 در حال آپلود ({format_size(file_size)})...", chat_id, status.message_id)

            with open(file_path, 'rb') as f:
                if quality == 'audio' or ext in ['.mp3', '.m4a', '.ogg']:
                    bot.send_audio(chat_id, f, caption="✅ دانلود شد!")
                elif ext in ['.mp4', '.mkv', '.webm', '.mov']:
                    bot.send_video(chat_id, f, caption="✅ دانلود شد!")
                elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    bot.send_photo(chat_id, f, caption="✅ دانلود شد!")
                else:
                    bot.send_document(chat_id, f, caption="✅ دانلود شد!")

            bot.delete_message(chat_id, status.message_id)

    except Exception as e:
        bot.edit_message_text("❌ خطا در دانلود. لینک ممکنه خصوصی یا محدود باشه.", chat_id, status.message_id)

@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.reply_to(message, "⚠️ لطفاً یه لینک معتبر بفرست!")

print("ربات شروع به کار کرد...")
bot.polling(none_stop=True)
