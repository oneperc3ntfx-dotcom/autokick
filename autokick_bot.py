import pytz
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler

# ==============================
# BOT TOKEN
# ==============================

BOT_TOKEN = "7678173969:AAFsD26EC2p4vyeTjxgGVSH3kMi_obIJ3k0"

bot = Bot(token=BOT_TOKEN)

# ==============================
# CHANNEL ID
# ==============================

PUBLIC_CHANNEL = "-1002605110502"
VIP_CHANNEL = "-1002782196938"

# ==============================
# GREETING PAGI
# ==============================

messages = {

"Monday": """🌅 Good Morning Traders! Happy Monday!

Hari baru, minggu baru, peluang baru di market! 📈

Trader sukses bukan yang selalu profit,
tetapi yang disiplin dengan strategi dan manajemen risiko.

Fokus trading hari ini:
✅ Analisa sebelum entry
✅ Jangan FOMO
✅ Ikuti trading plan

Semoga hari ini market memberikan peluang terbaik 💰

Let's catch the market together! 🚀""",

"Tuesday": """🌤 Selamat Pagi Trader Hebat! Happy Tuesday!

Market sudah bergerak sejak dini hari,
dan tugas kita bukan mengejar market… tetapi menunggu setup terbaik 🎯

Reminder hari ini:
📊 Ikuti analisa
📉 Jangan overtrade
🧠 Trading pakai logika bukan emosi

Semoga hari ini kita diberikan setup yang clean dan profit maksimal 💰📈""",

"Wednesday": """🌅 Good Morning Traders! Happy Wednesday!

Sudah pertengahan minggu 🔥

Biasanya market mulai menunjukkan arah yang lebih jelas.

Tips mentor hari ini:
📍 Fokus pada key level
📍 Tunggu konfirmasi
📍 Risk kecil peluang besar

Tetap disiplin dan nikmati proses menjadi trader konsisten 💪""",

"Thursday": """☀️ Selamat Pagi Traders! Happy Thursday!

Biasanya menjelang akhir minggu,
market mulai memberikan pergerakan menarik 📈

Checklist trader hari ini:
🔎 Analisa market structure
📊 Perhatikan news penting
⚖️ Jaga risk management

Semoga hari ini kita bisa menangkap momentum terbaik 🚀""",

"Friday": """🌅 Good Morning Traders! Happy Friday!

Hari terakhir trading minggu ini 🔥

Fokus kita hari ini:
📉 Hindari revenge trading
📊 Ambil setup yang jelas saja
💡 Protect profit minggu ini

Semoga closing minggu ini penuh pips 💰"""
}

# ==============================
# GREETING FUNCTION (07:00)
# ==============================

def send_greeting():

    tz = pytz.timezone("Asia/Jakarta")
    today = datetime.now(tz).strftime("%A")

    if today in messages:

        text = messages[today]

        try:
            bot.send_message(chat_id=PUBLIC_CHANNEL, text=text)
            bot.send_message(chat_id=VIP_CHANNEL, text=text)
            print("Greeting sent")
        except Exception as e:
            print(f"Error sending greeting: {e}")

# ==============================
# SIGNAL PREPARATION (07:30)
# PUBLIC CHANNEL ONLY
# ==============================

def send_signal_preparation():

    message = """⏰ Market Preparation Time

Signal trading akan mulai aktif pada pukul 08:00 WIB.

Sebelum market bergerak lebih aktif, pastikan kamu sudah melakukan persiapan:

💰 Pastikan equity siap
🧠 Siapkan mental trading yang disiplin
⚖️ Gunakan money management yang sehat
🚫 Hindari full margin dan over risk

Trading bukan tentang cepat kaya,
tetapi tentang konsistensi dan manajemen risiko.

Semoga hari ini market memberikan peluang terbaik untuk kita semua 📈✨
"""

    try:
        bot.send_message(chat_id=PUBLIC_CHANNEL, text=message)
        print("Preparation message sent")
    except Exception as e:
        print(f"Error sending preparation message: {e}")

# ==============================
# POLL MARKET (08:30)
# ==============================

def send_market_poll():

    question = """📊 Market Sentiment Poll

Menurut kamu arah XAUUSD hari ini?

Vote sekarang dan lihat mayoritas trader memilih arah market 🔥"""

    options = [
        "📈 BUY / Bullish",
        "📉 SELL / Bearish"
    ]

    try:

        bot.send_poll(
            chat_id=PUBLIC_CHANNEL,
            question=question,
            options=options,
            is_anonymous=False
        )

        bot.send_poll(
            chat_id=VIP_CHANNEL,
            question=question,
            options=options,
            is_anonymous=False
        )

        print("Poll sent")

    except Exception as e:
        print(f"Error sending poll: {e}")

# ==============================
# NIGHT MESSAGE (20:00)
# VIP CHANNEL ONLY
# ==============================

def send_night_message():

    message = """🌙 Selamat Malam Traders

Market hari ini telah memberikan banyak pergerakan.

Bagi yang sudah profit hari ini, selamat! 💰  
Bagi yang belum, jangan berkecil hati. Setiap hari di market selalu memberikan pelajaran berharga.

Dalam trading, yang paling penting bukan hanya hasil satu trade,
tetapi konsistensi dalam menjalankan strategi dan manajemen risiko.

Gunakan waktu malam ini untuk:
📊 Mereview trade hari ini  
🧠 Belajar dari setiap keputusan yang diambil  
📈 Mempersiapkan rencana trading untuk esok hari  

━━━━━━━━━━━━━━━

🚀 Ingin belajar trading lebih terarah?

Kami menyediakan:
📊 Komunitas trader yang solid
🤖 Signal dengan analisa AI
📈 Insight market harian

Dan semuanya bisa kamu akses gratis.

Jika kamu ingin bergabung, hubungi admin:

📩 @ADMOnePercentsFX
"""

    try:

        bot.send_message(chat_id=VIP_CHANNEL, text=message)
        print("Night message sent")

    except Exception as e:
        print(f"Error sending night message: {e}")

# ==============================
# SIGNAL CLOSED (21:30)
# PUBLIC CHANNEL ONLY
# ==============================

def send_signal_closed():

    message = """🌙 Trading Session Closed

Signal AI untuk hari ini telah resmi dinonaktifkan.

Semoga hasil trading hari ini memberikan profit yang baik dan membawa keberkahan untuk kita semua 💰✨

Terima kasih untuk disiplin dan kepercayaan kalian mengikuti signal hari ini.

Sekarang saatnya beristirahat dan memulihkan energi.

Besok kita akan kembali menghadapi market dengan strategi yang lebih siap 📊

Selamat beristirahat dan semoga malam kalian menyenangkan 🌙
"""

    try:
        bot.send_message(chat_id=PUBLIC_CHANNEL, text=message)
        print("Signal closed message sent")
    except Exception as e:
        print(f"Error sending closed message: {e}")

# ==============================
# PRIVATE CHAT REPLY
# ==============================

def start(update: Update, context: CallbackContext):

    update.message.reply_text(
        "🤖 Bot aktif!\n\n"
        "Schedule bot:\n"
        "🌅 Greeting 07:00\n"
        "⏰ Persiapan Signal 07:30\n"
        "📊 Poll Market 08:30\n"
        "🌙 VIP Night Message 20:00\n"
        "🔒 Signal Closed 21:30\n\n"
        "Ketik 'ping' untuk cek status."
    )

def reply_message(update: Update, context: CallbackContext):

    text = update.message.text.lower()

    if "ping" in text:
        update.message.reply_text("🏓 Pong! Bot aktif dan berjalan normal.")
    else:
        update.message.reply_text("Bot aktif ✅")

# ==============================
# TELEGRAM HANDLER
# ==============================

updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_message))

# ==============================
# SCHEDULER
# ==============================

scheduler = BackgroundScheduler(timezone="Asia/Jakarta")

scheduler.add_job(send_greeting, "cron", day_of_week="mon-fri", hour=7, minute=0)
scheduler.add_job(send_signal_preparation, "cron", day_of_week="mon-fri", hour=7, minute=30)
scheduler.add_job(send_market_poll, "cron", day_of_week="mon-fri", hour=8, minute=30)
scheduler.add_job(send_night_message, "cron", day_of_week="mon-fri", hour=20, minute=0)
scheduler.add_job(send_signal_closed, "cron", day_of_week="mon-fri", hour=21, minute=30)

scheduler.start()

print("Bot running...")

# ==============================
# START BOT
# ==============================

updater.start_polling()
updater.idle()
