#!/usr/bin/env python3

import os
import asyncio
import logging
import requests

from datetime import datetime, timedelta

import pytz
from dotenv import load_dotenv

from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from smc_engine import Candle, analyze

# ================= LOAD ENV =================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# PENTING: jangan taruh API key asli sebagai default value di kode.
# Set TWELVE_TOKEN di environment variable Railway / file .env lokal.
TWELVE_TOKEN = os.getenv("TWELVE_TOKEN")

CHAT_ID = int(os.getenv("CHAT_ID", "-1002605110502"))
THREAD_ID = int(os.getenv("THREAD_ID", "0"))

# Timeframe candle untuk struktur SMC. Bisa "1h" atau "15min".
SMC_INTERVAL = os.getenv("SMC_INTERVAL", "1h")
SMC_CANDLE_COUNT = int(os.getenv("SMC_CANDLE_COUNT", "60"))

# ================= TIMEZONE =================

WIB = pytz.timezone("Asia/Jakarta")

# ================= LOGGING =================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("XAU-BOT")

# ================= GLOBAL =================

cached_candles = None
cached_candles_time = None

last_signal_time = None
tasks_started = False

# ================= MARKET SESSION =================

def is_trading_time():

    now = datetime.now(WIB)

    day = now.weekday()
    hour = now.hour

    # Sabtu sampai jam 03:00 WIB
    if day == 5:
        return hour < 3

    # Minggu OFF
    if day == 6:
        return False

    # Senin mulai jam 07:00 WIB
    if day == 0:
        return hour >= 7

    # Selasa - Jumat ON
    return True


# ================= GET CANDLES =================

def get_candles(interval: str = None, count: int = None):
    """
    Ambil data candle OHLC dari Twelve Data (endpoint time_series).
    Dipakai untuk analisa struktur SMC, bukan cuma 1 titik harga.
    Cache 60 detik supaya hemat kuota API (free tier terbatas).
    """

    global cached_candles
    global cached_candles_time

    interval = interval or SMC_INTERVAL
    count = count or SMC_CANDLE_COUNT

    now = datetime.now(WIB)

    if (
        cached_candles is not None
        and cached_candles_time is not None
    ):
        diff = (now - cached_candles_time).total_seconds()
        if diff < 60:
            logger.info("USING CACHED CANDLES")
            return cached_candles

    if not TWELVE_TOKEN:
        logger.error("TWELVE_TOKEN belum di-set di environment variable")
        return cached_candles

    try:
        url = (
            "https://api.twelvedata.com/time_series"
            "?symbol=XAU/USD"
            f"&interval={interval}"
            f"&outputsize={count}"
            f"&apikey={TWELVE_TOKEN}"
        )

        response = requests.get(url, timeout=15)

        logger.info(f"TWELVEDATA STATUS: {response.status_code}")

        data = response.json()

        if data.get("status") == "error":
            logger.error(f"TWELVEDATA ERROR: {data.get('message')}")
            return cached_candles

        values = data.get("values")

        if not values:
            logger.error(f"TWELVEDATA: no values in response: {data}")
            return cached_candles

        # Twelve Data mengembalikan data dari yang TERBARU ke TERLAMA -> kita balik
        values = list(reversed(values))

        candles = [
            Candle(
                time=v["datetime"],
                open=float(v["open"]),
                high=float(v["high"]),
                low=float(v["low"]),
                close=float(v["close"]),
            )
            for v in values
        ]

        cached_candles = candles
        cached_candles_time = now

        logger.info(f"LIVE CANDLES: {len(candles)} bars, last close = {candles[-1].close}")

        return candles

    except Exception as e:
        logger.error(f"CANDLE FETCH ERROR: {e}")

    return cached_candles


def get_price():
    """Harga terkini = close candle terakhir."""
    candles = get_candles()
    if not candles:
        return None
    return candles[-1].close


# ================= BUILD SIGNAL =================

async def build_signal():

    if not is_trading_time():
        return "📴 MARKET CLOSED"

    candles = get_candles()

    if not candles:
        return "⚠️ No realtime price data"

    result = analyze(candles)

    entry = result.last_close
    now = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")

    if result.bias is None:
        reason_text = "\n".join([f"- {r}" for r in result.reasons])
        return f"""
📊 XAUUSD SIGNAL

🕒 {now} WIB

📈 BIAS: NO TRADE (struktur belum jelas / range)

📌 Harga sekarang: {entry:.2f}

🧠 ANALISA:
{reason_text}

━━━━━━━━━━━━
"""

    bias = result.bias

    # SL/TP fixed (pips), sesuai permintaan: TP1 +7, TP2 +15, SL -5
    if bias == "BUY":
        setup = "BUY LIMIT"
        tp1 = entry + 7
        tp2 = entry + 15
        sl = entry - 5
    else:
        setup = "SELL LIMIT"
        tp1 = entry - 7
        tp2 = entry - 15
        sl = entry + 5

    reason_text = "\n".join([f"- {r}" for r in result.reasons])

    return f"""
📊 XAUUSD SIGNAL

🕒 {now} WIB

📈 BIAS: {bias}
🔎 STRUKTUR: {result.structure}

📌 ENTRY: {setup} @ {entry:.2f}

🎯 TP1: {tp1:.2f}
🎯 TP2: {tp2:.2f}
⛔ SL : {sl:.2f}

🧠 REASON:
{reason_text}

⚠️ Ini hasil analisa otomatis berbasis aturan SMC, bukan saran finansial.
Selalu cross-check manual sebelum entry.
━━━━━━━━━━━━
"""


# ================= SEND MESSAGE =================

async def send(app, text):

    await app.bot.send_message(
        chat_id=CHAT_ID,
        message_thread_id=THREAD_ID,
        text=text
    )


# ================= SCHEDULER =================

async def scheduler(app):

    global last_signal_time

    while True:

        now = datetime.now(WIB)

        # ================= UBAH KE MENIT 00 =================
        next_run = now.replace(minute=0, second=0, microsecond=0)

        if now.minute >= 0:
            next_run += timedelta(hours=1)
        # ===================================================

        wait_time = (next_run - now).total_seconds()

        logger.info(f"NEXT SIGNAL: {next_run}")
        logger.info(f"WAITING {wait_time:.0f} SECONDS")

        await asyncio.sleep(wait_time)

        if not is_trading_time():
            logger.info("MARKET CLOSED")
            continue

        current_time = datetime.now(WIB).replace(second=0, microsecond=0)

        if last_signal_time == current_time:
            continue

        last_signal_time = current_time

        msg = await build_signal()

        await send(app, msg)

        logger.info("SIGNAL SENT")


# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 XAU BOT ACTIVE")


async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await build_signal()
    await update.message.reply_text(msg)


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):

    p = get_price()

    if p is None:
        return await update.message.reply_text("⚠️ No realtime price data")

    await update.message.reply_text(f"📈 XAUUSD: {p:.2f}")


# ================= POST INIT =================

async def post_init(app):

    global tasks_started

    if tasks_started:
        return

    tasks_started = True

    await app.bot.set_my_commands([
        BotCommand("start", "Start bot"),
        BotCommand("price", "Check XAUUSD price"),
        BotCommand("signal", "Generate signal")
    ])

    await send(app, "🤖 BOT ACTIVE")

    asyncio.create_task(scheduler(app))

    logger.info("BOT RUNNING STABLE")


# ================= MAIN =================

def main():

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN belum di-set di environment variable")

    if not TWELVE_TOKEN:
        logger.warning("TWELVE_TOKEN belum di-set! Bot akan jalan tapi tidak bisa ambil data harga.")

    logger.info("STARTING BOT...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("signal", signal))

    app.post_init = post_init

    app.run_polling(drop_pending_updates=True, close_loop=False)


if __name__ == "__main__":
    main()
