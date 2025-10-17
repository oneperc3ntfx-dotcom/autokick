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
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "7868818205:AAEXyn7KXmgVzW2wSZuJuXpwcQtVP6BFL2E")
TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "-1002605110502"))  # ID grup
ADMIN_ID = int(os.getenv("ADMIN_ID", "1305881282"))  # ID admin
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

# === KIRIM OPSI KE ADMIN ===
async def send_options_to_admin(bot, user):
    """Kirim tombol pilihan ke chat pribadi admin"""
    user_id = str(user.id)
    data = load_data()
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

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"👤 Member baru: @{user.username or user.full_name}\nPilih opsi:",
        reply_markup=keyboard
    )
    print(f"🔔 Opsi untuk @{user.username or user.full_name} dikirim ke admin.")

# === CHAT MEMBER HANDLER ===
async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.chat_member:
        return
    chat = update.chat_member.chat
    if chat.id != TARGET_CHAT_ID:
        return

    old_status = update.chat_member.old_chat_member.status
    new_status = update.chat_member.new_chat_member.status
    user = update.chat_member.new_chat_member.user

    # Member baru masuk → ucapkan selamat datang di grup
    if old_status in [ChatMember.LEFT, ChatMember.KICKED] and new_status == ChatMember.MEMBER:
        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=f"👋 Selamat datang @{user.username or user.full_name}!\n💰 Semoga berhasil cuan! 🚀"
        )
        await send_options_to_admin(context.bot, user)

# === MESSAGE HANDLER UNTUK JOIN VIA LINK ===
async def new_member_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    for user in update.message.new_chat_members:
        # Selamat datang di grup
        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=f"👋 Selamat datang @{user.username or user.full_name}!\n💰 Semoga berhasil cuan! 🚀"
        )
        await send_options_to_admin(context.bot, user)

# === BUTTON CALLBACK ADMIN ===
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.data.split("_")[1]
    data = load_data()

    if user_id not in data:
        return

    if query.data.startswith("perm"):
        data[user_id]["status"] = "permanent"
        await query.edit_message_text(f"✅ @{data[user_id]['username']} ditetapkan permanen.")
    elif query.data.startswith("24h"):
        data[user_id]["status"] = "24h"
        await query.edit_message_text(f"⏳ @{data[user_id]['username']} akan dikeluarkan otomatis setelah 24 jam.")

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

            try:
                if status == "pending" and elapsed > timedelta(minutes=10):
                    await app.bot.ban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.unban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.send_message(
                        TARGET_CHAT_ID,
                        f"⏰ @{info['username']} tidak memilih opsi, dikeluarkan otomatis."
                    )
                    print(f"❌ Kicked @{info['username']} (no response).")
                    del data[user_id]
                    changed = True

                elif status == "24h" and elapsed > timedelta(hours=24):
                    await app.bot.ban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.unban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.send_message(
                        TARGET_CHAT_ID,
                        f"❌ @{info['username']} sudah 24 jam, dikeluarkan otomatis."
                    )
                    print(f"❌ Kicked @{info['username']} (24 jam habis).")
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
    await app.bot.send_message(ADMIN_ID, "✅ Bot AutoKick sudah aktif dan memantau grup.")
    await app.bot.send_message(TARGET_CHAT_ID, "👋 Halo, aku datang! Bot AutoKick sudah aktif.")

# === MAIN ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_start).build()
    app.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    print("🤖 Bot AutoKick aktif dan memantau grup...")
    app.run_polling()

if __name__ == "__main__":
    main()
