import telebot
import yt_dlp
import os
import tempfile
from pathlib import Path

BOT_TOKEN = "8764355663:AAGe2uMmOBPCEqsPTFzlr6PJoALQEuLzEps"
MAX_FILE_MB = 50

bot = telebot.TeleBot(BOT_TOKEN)

def format_size(b):
    return f"{b/(1024*1024):.1f} MB"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
        "سلام! به ربات دانلودر خوش اومدی!\n\n"
        "کافیه لینک ویدیو یا عکست رو بفرستی.\n\n"
        "پشتیبانی از:\n"
        "YouTube, Instagram, TikTok, Pinterest و بیشتر!"
    )

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message,
        "طرز استفاده:\n\n"
        "1. لینک رو کپی کن\n"
        "2. اینجا بفرست\n"
        "3. صبر کن دانلود بشه\n"
        "4. فایلت رو دریافت کن!"
    )

@bot.message_handler(func=lambda m: m.text and m.text.startswith('http'))
def handle_link(message):
    url = message.text.strip()
    status = bot.reply_to(message, "در حال دانلود... صبر کن.")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'outtmpl': os.path.join(tmpdir, '%(title).50s.%(ext)s'),
                'format': 'best[filesize<45M]/best',
                'quiet': True,
                'noplaylist': True,
                'max_filesize': 45 * 1024 * 1024,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            files = list(Path(tmpdir).iterdir())
            if not files:
                bot.edit_message_text("دانلود ناموفق بود.", message.chat.id, status.message_id)
                return
            file_path = str(files[0])
            file_size = os.path.getsize(file_path)
            ext = Path(file_path).suffix.lower()
            if file_size > MAX_FILE_MB * 1024 * 1024:
                bot.edit_message_text(f"فایل خیلی بزرگه ({format_size(file_size)}).", message.chat.id, status.message_id)
                return
            bot.edit_message_text(f"در حال آپلود ({format_size(file_size)})...", message.chat.id, status.message_id)
            with open(file_path, 'rb') as f:
                if ext in ['.mp4', '.mkv', '.webm', '.mov']:
                    bot.send_video(message.chat.id, f, caption="دانلود شد!")
                elif ext in ['.mp3', '.m4a', '.ogg']:
                    bot.send_audio(message.chat.id, f, caption="دانلود شد!")
                elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    bot.send_photo(message.chat.id, f, caption="دانلود شد!")
                else:
                    bot.send_document(message.chat.id, f, caption="دانلود شد!")
            bot.delete_message(message.chat.id, status.message_id)
    except Exception as e:
        bot.edit_message_text("خطا در دانلود. لینک ممکنه خصوصی یا محدود باشه.", message.chat.id, status.message_id)

@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.reply_to(message, "لطفا یه لینک معتبر بفرست!")

print("ربات شروع به کار کرد...")
bot.polling(none_stop=True)
O

