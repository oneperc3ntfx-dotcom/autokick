import pytz
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler

# ==============================
# BOT TOKEN
# ==============================

BOT_TOKEN = 7678173969:AAFsD26EC2p4vyeTjxgGVSH3kMi_obIJ3k0"

# ==============================
# CHANNEL ID
# ==============================

CHANNELS = [
    "-1003142698012",
    "-1002782196938"
]

bot = Bot(token=BOT_TOKEN)

# ==============================
# GREETING PAGI
# ==============================

messages = {

"Monday": """🌅 Good Morning Traders! Happy Monday!

Hari baru, minggu baru, peluang baru di market! 📈
Ingat, trader sukses bukan yang selalu profit, tapi yang konsisten dengan disiplin dan manajemen risiko.

Hari ini fokus kita:
✅ Analisa sebelum entry
✅ Jangan FOMO
✅ Ikuti trading plan

Market selalu memberi peluang bagi yang sabar.
Mari mulai minggu ini dengan mindset professional trader 💪

Semoga hari ini penuh pips! 🔥
Let's catch the market together! 🚀""",

"Tuesday": """🌤 Selamat Pagi Trader Hebat! Happy Tuesday!

Market sudah bergerak sejak dini hari, dan tugas kita bukan mengejar market… tapi menunggu setup terbaik 🎯

Reminder pagi ini:
📊 Ikuti analisa
📉 Jangan overtrade
🧠 Trading pakai logika, bukan emosi

Semoga hari ini kita diberikan setup yang clean dan profit maksimal 💰📈""",

"Wednesday": """🌅 Good Morning Traders! Happy Wednesday!

Sudah pertengahan minggu! 🔥
Market biasanya mulai menunjukkan arah yang lebih jelas.

Tips mentor pagi ini:
📍 Fokus pada key level
📍 Tunggu konfirmasi sebelum entry
📍 Risk kecil, peluang besar

Tetap disiplin dan nikmati proses menjadi trader yang konsisten 💪📊""",

"Thursday": """☀️ Selamat Pagi Traders! Happy Thursday!

Biasanya menjelang akhir minggu, market mulai memberikan pergerakan yang menarik 📈

Checklist trader pagi ini:
🔎 Analisa market structure
📊 Perhatikan news penting
⚖️ Jaga risk management

Semoga hari ini kita bisa menangkap momentum terbaik di market 🚀💰""",

"Friday": """🌅 Good Morning Traders! Happy Friday!

Hari terakhir trading minggu ini! 🔥
Fokus kita hari ini bukan hanya profit, tapi menutup minggu dengan disiplin.

📉 Hindari revenge trading
📊 Ambil setup yang jelas saja
💡 Protect profit minggu ini

Semoga closing minggu ini penuh pips! 💰"""
}

# ==============================
# SEND GREETING
# ==============================

def send_greeting():

    tz = pytz.timezone("Asia/Jakarta")
    today = datetime.now(tz).strftime("%A")

    if today in messages:

        text = messages[today]

        for channel in CHANNELS:
            bot.send_message(chat_id=channel, text=text)

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

    for channel in CHANNELS:

        bot.send_poll(
            chat_id=channel,
            question=question,
            options=options,
            is_anonymous=False
        )

# ==============================
# NIGHT MESSAGE
# ==============================

def send_night_message():

    text = """🌙 Selamat Malam Traders

Market hari ini telah memberikan banyak pergerakan.
Bagi yang sudah profit hari ini, selamat! 💰
Bagi yang belum, ingat bahwa trading adalah proses belajar yang konsisten.

━━━━━━━━━━━━━━━

🚨 Banyak Trader Sudah Mulai Profit dari Analisa AI XAUUSD… Kamu Masih Nonton?

Setiap hari market Gold (XAUUSD) bergerak puluhan hingga ratusan pips 📈
Dan banyak member kami sudah mulai menangkap peluang tersebut bersama komunitas VIP.

Pertanyaannya sekarang…

❓ Kamu mau ikut ambil peluangnya
atau hanya melihat orang lain yang cuan?

Di Channel VIP, kamu akan mendapatkan:

🔥 Analisa market harian XAUUSD
🤖 Sistem analisa dengan bantuan AI
📊 Potensi setup entry yang jelas
🧠 Edukasi mindset & manajemen risiko
👥 Komunitas trader yang aktif

⚠️ Jangan sampai kamu menyesal karena terlambat join.

Market selalu bergerak…
tapi peluang terbaik biasanya dimanfaatkan oleh trader yang siap.

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

💰 Kesempatan tidak datang dua kali.

Jika kamu serius ingin belajar trading dan entry bersama komunitas,
hubungi admin sekarang sebelum kamu melewatkan peluang berikutnya.

📩 Chat Admin
👇👇👇
@ADMOnePercentsFX
"""

    for channel in CHANNELS:
        bot.send_message(chat_id=channel, text=text)

# ==============================
# PRIVATE CHAT
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
# HANDLER
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
