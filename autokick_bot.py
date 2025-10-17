import json
import asyncio
import os
from datetime import datetime, timedelta
from telegram import Update, ChatMember, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    ChatMemberHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import pytz

# =============================
# KONFIGURASI
# =============================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8196752676:AAEWUiQtvwGgwVbh6UDV-RxqwHk-3CYKnGA")
TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "-1003143901775"))
JKT = pytz.timezone("Asia/Jakarta")
DATA_FILE = "members.json"


# =============================
# UTILITAS
# =============================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# =============================
# CALLBACK TOMBOL USER
# =============================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_data()

    if user_id not in data:
        await query.answer("Data kamu tidak ditemukan.")
        return

    if query.data == "permanent":
        data[user_id]["mode"] = "permanent"
        save_data(data)
        await query.edit_message_text("✅ Kamu dipilih sebagai anggota *permanent*.")
    elif query.data == "24jam":
        data[user_id]["mode"] = "24jam"
        save_data(data)
        await query.edit_message_text("✅ Kamu akan otomatis dikeluarkan setelah 24 jam.")

    await query.answer()


# =============================
# EVENT MEMBER JOIN
# =============================
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
            "mode": None,
        }
        save_data(data)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Permanent", callback_data="permanent"),
                InlineKeyboardButton("⏳ 24 Jam", callback_data="24jam")
            ]
        ])

        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=(
                f"👋 @{user.username or user.full_name} baru bergabung.\n"
                f"Pilih jenis keanggotaan kamu dalam 10 menit:\n"
                f"- Permanent: Tidak akan dikeluarkan\n"
                f"- 24 Jam: Dikeluarkan otomatis setelah 24 jam\n\n"
                f"Jika tidak memilih dalam 10 menit, kamu akan dikeluarkan."
            ),
            reply_markup=keyboard
        )


# =============================
# AUTO KICK TASK
# =============================
async def auto_kick_task(app):
    print("⚙️ Background auto-kick task dimulai...")
    while True:
        data = load_data()
        now = datetime.now(JKT)
        changed = False

        for user_id, info in list(data.items()):
            join_time = datetime.fromisoformat(info["join_time"])
            mode = info.get("mode")

            if mode == "permanent":
                continue

            if mode is None and (now - join_time) >= timedelta(minutes=10):
                try:
                    await app.bot.ban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.unban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.send_message(
                        chat_id=TARGET_CHAT_ID,
                        text=f"❌ @{info['username']} tidak memilih, dikeluarkan setelah 10 menit."
                    )
                    del data[user_id]
                    changed = True
                except Exception as e:
                    print(f"⚠️ Gagal kick {user_id}: {e}")

            elif mode == "24jam" and (now - join_time) >= timedelta(hours=24):
                try:
                    await app.bot.ban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.unban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.send_message(
                        chat_id=TARGET_CHAT_ID,
                        text=f"⏰ @{info['username']} dikeluarkan setelah 24 jam di grup."
                    )
                    del data[user_id]
                    changed = True
                except Exception as e:
                    print(f"⚠️ Gagal kick {user_id}: {e}")

        if changed:
            save_data(data)

        await asyncio.sleep(60)


# =============================
# JALANKAN BOT
# =============================
async def on_start(app):
    """Dipanggil setelah bot aktif — mulai background task di sini."""
    asyncio.create_task(auto_kick_task(app))
    print("🤖 Bot AutoKick aktif dan memantau grup...")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_start).build()
    app.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling(stop_signals=None)


if __name__ == "__main__":
    main()
