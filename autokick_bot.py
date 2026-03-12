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

PUBLIC_CHANNEL = "-1003142698012"
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
# GREETING FUNCTION
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
# POLL MARKET
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
# NIGHT MESSAGE
# ==============================

def send_night_message():

    message_public = """🌙 Selamat Malam Traders

Market hari ini telah memberikan banyak pergerakan.

Bagi yang sudah profit hari ini, selamat! 💰
Bagi yang belum, jadikan hari ini sebagai pelajaran untuk menjadi trader yang lebih baik.

Ingat:
Trader sukses bukan yang selalu menang,
tetapi yang konsisten belajar dan disiplin menjalankan strategi.

Istirahat yang cukup malam ini,
karena market besok selalu memberikan peluang baru 📈

See you tomorrow traders 🚀
"""

    message_vip = """🌙 Selamat Malam Traders

Market hari ini kembali memberikan pergerakan menarik pada XAUUSD.

Banyak trader sudah mulai memanfaatkan peluang tersebut dengan bantuan analisa yang lebih terarah.

━━━━━━━━━━━━━━━

🚨 Banyak Trader Sudah Mulai Profit dari Analisa AI XAUUSD… Kamu Masih Nonton?

Setiap hari market Gold bergerak puluhan hingga ratusan pips 📈  
Dan banyak member kami sudah mulai menangkap peluang tersebut bersama komunitas VIP.

Di Channel VIP kamu akan mendapatkan:

🔥 Analisa market harian XAUUSD  
🤖 Sistem analisa dengan bantuan AI  
📊 Setup entry yang lebih jelas  
🧠 Edukasi mindset & manajemen risiko  
👥 Komunitas trader yang aktif

Market selalu bergerak…
tetapi peluang terbaik biasanya dimanfaatkan oleh trader yang siap.

━━━━━━━━━━━━━━━

📌 Gunakan broker yang sama dengan komunitas kami

👉 BROKER HFM
https://register.hfmtrade-ind.com/sv/en/new-live-account/?refid=333604&acid=s2x4c6usld

📚 Panduan Lengkap:

📌 Cara Daftar HFM
https://t.me/+in9fqf4PrSYxYTM9

📌 Cara Tautkan ke MT5
https://t.me/+eb2Ky1Iva2Y5MTRl

📌 Cara Pindah Mitra
https://t.me/+nPQJou-Y-tw5NzQ1

━━━━━━━━━━━━━━━

Jika kamu serius ingin belajar trading dan entry bersama komunitas,
hubungi admin sekarang.

📩 Chat Admin
👇👇👇
@ADMOnePercentsFX
"""

    try:

        bot.send_message(chat_id=PUBLIC_CHANNEL, text=message_public)

        bot.send_message(chat_id=VIP_CHANNEL, text=message_vip)

        print("Night message sent")

    except Exception as e:
        print(f"Error sending night message: {e}")

# ==============================
# PRIVATE CHAT REPLY
# ==============================

def start(update: Update, context: CallbackContext):

    update.message.reply_text(
        "🤖 Bot aktif!\n\n"
        "Schedule bot:\n"
        "🌅 Greeting 07:00\n"
        "📊 Poll Market 08:30\n"
        "🌙 Night Message 20:00\n\n"
        "Ketik 'ping' untuk cek status."
    )

def reply_message(update: Update, context: CallbackContext):

    text = update.message.text.lower()

    if "ping" in text:
        update.message.reply_text("🏓 Pong! Bot aktif dan berjalan dengan normal.")
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

scheduler.add_job(send_market_poll, "cron", day_of_week="mon-fri", hour=8, minute=30)

scheduler.add_job(send_night_message, "cron", day_of_week="mon-fri", hour=20, minute=0)

scheduler.start()

print("Bot running...")

# ==============================
# START BOT
# ==============================

updater.start_polling()
updater.idle()
