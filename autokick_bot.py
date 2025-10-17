#!/usr/bin/env python3
import os
import json
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Update, ChatMember, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    ChatMemberHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
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

# === MEMBER HANDLER ===
async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.chat_member:
        return
    chat = update.chat_member.chat
    if chat.id != TARGET_CHAT_ID:
        return

    old_status = update.chat_member.old_chat_member.status
    new_status = update.chat_member.new_chat_member.status
    user = update.chat_member.new_chat_member.user

    if old_status in [ChatMember.LEFT, ChatMember.KICKED] and new_status == ChatMember.MEMBER:
        data = load_data()
        user_id = str(user.id)
        join_time = datetime.now(JKT).isoformat()
        data[user_id] = {
            "username": user.username or user.full_name,
            "join_time": join_time,
            "status": "pending"
        }
        save_data(data)

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

# === AUTO KICK TASK ===
async def auto_kick_task(app):
    while True:
        data = load_data()
        now = datetime.now(JKT)
        changed = False

        for user_id, info in list(data.items()):
            join_time = datetime.fromisoformat(info["join_time"])
            status = info.get("status", "pending")
            elapsed = now - join_time

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
    app.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_callback))
    print("🤖 Bot AutoKick aktif dan memantau grup...")
    app.run_polling()

if __name__ == "__main__":
    main()
