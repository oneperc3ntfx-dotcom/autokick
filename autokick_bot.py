#!/usr/bin/env python3
import os
import json
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    ChatMemberHandler, CallbackQueryHandler
)

# =====================
# KONFIGURASI
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ISI_TOKEN_KAMU")
TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "-1003143901775"))
JKT = pytz.timezone("Asia/Jakarta")
DATA_FILE = "members.json"

# =====================
# UTILITAS FILE
# =====================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# EVENT MEMBER JOIN
# =====================
async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.chat_member:
        return
    chat = update.chat_member.chat
    if chat.id != TARGET_CHAT_ID:
        return

    old_status = update.chat_member.old_chat_member.status
    new_status = update.chat_member.new_chat_member.status
    user = update.chat_member.new_chat_member.user

    # hanya saat baru join
    if old_status in [ChatMember.LEFT, ChatMember.KICKED] and new_status == ChatMember.MEMBER:
        data = load_data()
        user_id = str(user.id)
        now = datetime.now(JKT).isoformat()
        data[user_id] = {"username": user.username or user.full_name, "join_time": now, "mode": None}
        save_data(data)

        keyboard = [
            [
                InlineKeyboardButton("🔒 Permanen", callback_data=f"permanent:{user_id}"),
                InlineKeyboardButton("⏳ 24 Jam", callback_data=f"24h:{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=f"👋 @{user.username or user.full_name} baru bergabung.\n"
                 f"Silakan pilih durasi keanggotaan dalam 10 menit, "
                 f"jika tidak akan otomatis dikeluarkan.",
            reply_markup=reply_markup
        )
        print(f"✅ {user.full_name} join, menunggu pilihan.")

# =====================
# HANDLER PILIHAN USER
# =====================
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    user_id = query.data.split(":")[1]
    user_choice = query.data.split(":")[0]

    if user_id not in data:
        await query.edit_message_text("⚠️ Data tidak ditemukan.")
        return

    data[user_id]["mode"] = user_choice
    save_data(data)

    if user_choice == "permanent":
        await query.edit_message_text("✅ Keanggotaan diatur menjadi *permanen*.", parse_mode="Markdown")
        print(f"🔒 {data[user_id]['username']} set permanen.")
    elif user_choice == "24h":
        await query.edit_message_text("✅ Keanggotaan diatur selama *24 jam*.", parse_mode="Markdown")
        print(f"⏳ {data[user_id]['username']} set 24 jam.")

# =====================
# AUTO-KICK TASK
# =====================
async def auto_kick_task(app):
    while True:
        data = load_data()
        now = datetime.now(JKT)
        changed = False

        for user_id, info in list(data.items()):
            mode = info.get("mode")
            join_time = datetime.fromisoformat(info["join_time"])

            if mode == "permanent":
                continue
            elif mode == "24h" and now - join_time >= timedelta(hours=24):
                reason = "24 jam"
            elif mode is None and now - join_time >= timedelta(minutes=10):
                reason = "tidak memilih (10 menit)"
            else:
                continue

            try:
                await app.bot.ban_chat_member(TARGET_CHAT_ID, int(user_id))
                await app.bot.unban_chat_member(TARGET_CHAT_ID, int(user_id))
                await app.bot.send_message(
                    chat_id=TARGET_CHAT_ID,
                    text=f"❌ @{info['username']} dikeluarkan ({reason})."
                )
                print(f"❌ {info['username']} dikeluarkan ({reason}).")
                del data[user_id]
                changed = True
            except Exception as e:
                print(f"⚠️ Gagal kick {user_id}: {e}")

        if changed:
            save_data(data)

        await asyncio.sleep(60)  # cek tiap menit

# =====================
# MAIN FUNCTION
# =====================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_click))

    asyncio.create_task(auto_kick_task(app))

    print("🤖 Bot AutoKick aktif dan memantau grup...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
