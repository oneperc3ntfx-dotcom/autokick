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
    ContextTypes,
    filters,
)

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "8196752676:AAEWUiQtvwGgwVbh6UDV-RxqwHk-3CYKnGA")
TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "-1003143901775"))  # ganti ID grup kamu
ADMIN_ID = int(os.getenv("ADMIN_ID", "1305881282"))  # ID kamu
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

# === KIRIM OPSI JOIN ===
async def send_join_options(bot, user, username_display):
    """Kirim tombol opsi ke grup"""
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

    await bot.send_message(
        chat_id=TARGET_CHAT_ID,
        text=f"👋 {username_display} baru bergabung.\n"
             f"Silakan pilih opsi dalam **10 menit**, jika tidak akan dikeluarkan otomatis.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    print(f"👋 {username_display} joined, menunggu pilihan...")

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

    print(f"🔄 {user.full_name} status berubah dari {old_status} → {new_status}")

    if old_status in [ChatMember.LEFT, ChatMember.KICKED] and new_status == ChatMember.MEMBER:
        await send_join_options(context.bot, user, f"@{user.username or user.full_name}")

# === MESSAGE HANDLER UNTUK JOIN VIA LINK ===
async def new_member_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await send_join_options(context.bot, user, f"@{user.username or user.full_name} (via link)")

# === BUTTON CALLBACK ===
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
    # Kirim pesan ke admin pribadi
    await app.bot.send_message(ADMIN_ID, "✅ Bot AutoKick sudah aktif dan memantau grup.")
    # Kirim pesan ke grup target saat deploy
    await app.bot.send_message(TARGET_CHAT_ID, "👋 Halo! Aku datang dan siap memantau grup. Pilih opsi join untuk member baru.")
    # Mulai task auto kick
    asyncio.create_task(auto_kick_task(app))

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
