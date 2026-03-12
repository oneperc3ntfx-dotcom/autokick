import pytz
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler

# ==============================
# BOT TOKEN
# ==============================

BOT_TOKEN = "7678173969:AAFsD26EC2p4vyeTjxgGVSH3kMi_obIJ3k0"

# ==============================
# CHANNEL ID
# ==============================

CHANNELS = [
    "-1003142698012",
    "-1002782196938"
]

bot = Bot(token=BOT_TOKEN)

# ==============================
# GREETING MESSAGES
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

Trader profesional tahu kapan masuk market dan kapan menunggu.

Semoga hari ini kita diberikan setup yang clean dan profit maksimal 💰📈""",

"Wednesday": """🌅 Good Morning Traders! Happy Wednesday!

Sudah pertengahan minggu! 🔥
Market biasanya mulai menunjukkan arah yang lebih jelas.

Tips mentor pagi ini:
📍 Fokus pada key level
📍 Tunggu konfirmasi sebelum entry
📍 Risk kecil, peluang besar

Ingat, 1 trade bagus lebih baik daripada 10 trade terburu-buru.

Tetap disiplin dan nikmati proses menjadi trader yang konsisten 💪📊""",

"Thursday": """☀️ Selamat Pagi Traders! Happy Thursday!

Biasanya menjelang akhir minggu, market mulai memberikan pergerakan yang menarik 📈

Checklist trader pagi ini:
🔎 Analisa market structure
📊 Perhatikan news penting
⚖️ Jaga risk management

Jangan lupa:
Profit besar datang dari kesabaran dan strategi yang tepat.

Semoga hari ini kita bisa menangkap momentum terbaik di market 🚀💰""",

"Friday": """🌅 Good Morning Traders! Happy Friday!

Hari terakhir trading minggu ini! 🔥
Fokus kita hari ini bukan hanya profit, tapi menutup minggu dengan disiplin.

Reminder dari mentor:
📉 Hindari revenge trading
📊 Ambil setup yang jelas saja
💡 Protect profit minggu ini

Trader profesional tahu kapan mengunci profit dan berhenti trading.

Semoga closing minggu ini penuh pips! 💰
See you at the top traders! 🚀"""
}

# ==============================
# SEND GREETING FUNCTION
# ==============================

def send_greeting():

    tz = pytz.timezone("Asia/Jakarta")
    today = datetime.now(tz).strftime("%A")

    if today in messages:

        text = messages[today]

        for channel in CHANNELS:
            try:
                bot.send_message(chat_id=channel, text=text)
                print(f"Message sent to {channel}")
            except Exception as e:
                print(f"Error sending message: {e}")

# ==============================
# PRIVATE CHAT REPLY
# ==============================

def start(update: Update, context: CallbackContext):

    update.message.reply_text(
        "🤖 Bot aktif!\n\n"
        "Bot ini mengirim greeting otomatis ke channel setiap hari kerja jam 07:00 WIB.\n\n"
        "Kirim 'ping' untuk mengecek status bot."
    )

def reply_message(update: Update, context: CallbackContext):

    text = update.message.text.lower()

    if "ping" in text:
        update.message.reply_text("🏓 Pong! Bot aktif dan berjalan dengan normal.")

    else:
        update.message.reply_text(
            "👋 Halo!\n\n"
            "Bot sedang aktif.\n"
            "Greeting otomatis dikirim setiap Senin - Jumat jam 07:00 WIB."
        )

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

scheduler.add_job(
    send_greeting,
    "cron",
    day_of_week="mon-fri",
    hour=7,
    minute=0
)

scheduler.start()

print("Bot running... Greeting will be sent every weekday at 07:00 WIB")

# ==============================
# START BOT
# ==============================

updater.start_polling()
updater.idle()
