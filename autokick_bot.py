#!/usr/bin/env python3
import os
import json
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "8196752676:AAEWUiQtvwGgwVbh6UDV-RxqwHk-3CYKnGA")
TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "-1003143901775"))
JKT = pytz.timezone("Asia/Jakarta")
DATA_FILE = "members.json"

# === DATA HANDLING ===
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# === NEW MEMBER HANDLER (pasti terdeteksi) ===
async def new_member_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    chat = update.effective_chat
    if chat.id != TARGET_CHAT_ID:
        return

    data = load_data()
    for user in update.message.new_chat_members:
        user_id = str(user.id)
        join_time = datetime.now(JKT).isoformat()
        data[user_id] = {
            "username": user.username or user.full_name,
            "join_time": join_time,
            "status": "pending"
        }

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Permanen", callback_data=f"perm_{user_id}")],
            [InlineKeyboardButton("⏳ 24 Jam", callback_data=f"24h_{user_id}")]
        ])
        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=f"👋 @{user.username or user.full_name} baru bergabung.\n"
                 f"Silakan pilih opsi dalam 10 menit, jika tidak akan dikeluarkan otomatis.",
            reply_markup=keyboard
        )
        print(f"👋 {user.full_name} joined. Awaiting choice...")

    save_data(data)

# === BUTTON HANDLER ===
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.data.split("_")[1]
    data = load_data()
    if user_id not in data:
        return
    if query.data.startswith("perm"):
        data[user_id]["status"] = "permanent"
        await query.edit_message_text("✅ Ditetapkan permanen, tidak akan dikeluarkan.")
    elif query.data.startswith("24h"):
        data[user_id]["status"] = "24h"
        await query.edit_message_text("⏳ Akan dikeluarkan otomatis setelah 24 jam.")
    save_data(data)

# === AUTO KICK LOOP ===
async def auto_kick_task(app):
    while True:
        data = load_data()
        now = datetime.now(JKT)
        changed = False

        for user_id, info in list(data.items()):
            join_time = datetime.fromisoformat(info["join_time"])
            status = info.get("status", "pending")
            elapsed = now - join_time

            # Tidak memilih dalam 10 menit
            if status == "pending" and elapsed > timedelta(minutes=10):
                try:
                    await app.bot.ban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.unban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.send_message(TARGET_CHAT_ID,
                        f"⏰ @{info['username']} tidak memilih opsi, dikeluarkan otomatis.")
                    print(f"❌ Kicked @{info['username']} (no response).")
                    del data[user_id]
                    changed = True
                except Exception as e:
                    print(f"⚠️ Kick error: {e}")

            # 24 jam berlalu
            elif status == "24h" and elapsed > timedelta(hours=24):
                try:
                    await app.bot.ban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.unban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.send_message(TARGET_CHAT_ID,
                        f"❌ @{info['username']} sudah 24 jam, dikeluarkan otomatis.")
                    print(f"❌ Kicked @{info['username']} (24h expired).")
                    del data[user_id]
                    changed = True
                except Exception as e:
                    print(f"⚠️ Kick error: {e}")

        if changed:
            save_data(data)
        await asyncio.sleep(60)

# === STARTUP ===
async def on_start(app):
    asyncio.create_task(auto_kick_task(app))

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_start).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    print("🤖 Bot AutoKick aktif dan memantau grup...")
    app.run_polling()

if __name__ == "__main__":
    main()
