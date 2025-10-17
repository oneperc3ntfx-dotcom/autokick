#!/usr/bin/env python3
import json
import asyncio
import os
from datetime import datetime, timedelta
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    ChatMemberHandler,
)
import pytz

# =============================
# KONFIGURASI
# =============================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8196752676:AAEWUiQtvwGgwVbh6UDV-RxqwHk-3CYKnGA")
TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "-1003143901775"))
KICK_MODE = os.getenv("KICK_MODE", "").upper()  # PILIH: "PERMANENT", "24H", atau kosong (default = 10 menit)
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
# EVENT HANDLER
# =============================
async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cek jika ada member baru bergabung"""
    if not update.chat_member:
        return

    chat = update.chat_member.chat
    if chat.id != TARGET_CHAT_ID:
        return

    old_status = update.chat_member.old_chat_member.status
    new_status = update.chat_member.new_chat_member.status
    user = update.chat_member.new_chat_member.user

    if old_status in [ChatMember.LEFT, ChatMember.KICKED] and new_status == ChatMember.MEMBER:
        # =============================
        # MODE PERMANEN
        # =============================
        if KICK_MODE == "PERMANENT":
            print(f"✅ @{user.username or user.full_name} bergabung (mode permanen, tidak akan di-kick).")
            await context.bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text=f"👋 @{user.username or user.full_name} bergabung.\n✅ Mode *PERMANENT* aktif — member tidak akan dihapus.",
                parse_mode="Markdown"
            )
            return

        # =============================
        # MODE 24 JAM ATAU 10 MENIT
        # =============================
        data = load_data()
        user_id = str(user.id)
        join_time = datetime.now(JKT).isoformat()

        if KICK_MODE == "24H":
            kick_after = 24 * 60  # menit
            mode_text = "24 jam"
        else:
            kick_after = 10  # default = 10 menit
            mode_text = "10 menit (default)"

        data[user_id] = {
            "username": user.username or user.full_name,
            "join_time": join_time,
            "kick_after": kick_after
        }
        save_data(data)

        print(f"👋 {user.full_name} bergabung. Akan dikeluarkan setelah {mode_text}.")
        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=f"👋 @{user.username or user.full_name} baru bergabung.\n⏳ Akan otomatis dikeluarkan setelah *{mode_text}*.",
            parse_mode="Markdown"
        )


# =============================
# TUGAS OTOMATIS (KICK)
# =============================
async def auto_kick_task(app):
    if KICK_MODE == "PERMANENT":
        print("⏩ Mode PERMANENT aktif — auto kick dinonaktifkan.")
        return

    while True:
        data = load_data()
        now = datetime.now(JKT)
        changed = False

        for user_id, info in list(data.items()):
            join_time = datetime.fromisoformat(info["join_time"])
            kick_after = info.get("kick_after", 10)
            if now - join_time >= timedelta(minutes=kick_after):
                try:
                    await app.bot.ban_chat_member(TARGET_CHAT_ID, int(user_id))
                    await app.bot.unban_chat_member(TARGET_CHAT_ID, int(user_id))
                    print(f"❌ @{info['username']} dikeluarkan ({kick_after} menit berlalu).")
                    await app.bot.send_message(
                        chat_id=TARGET_CHAT_ID,
                        text=f"❌ @{info['username']} telah dikeluarkan setelah *{kick_after} menit* di grup.",
                        parse_mode="Markdown"
                    )
                    del data[user_id]
                    changed = True
                except Exception as e:
                    print(f"⚠️ Gagal kick {user_id}: {e}")

        if changed:
            save_data(data)

        await asyncio.sleep(60)  # cek tiap menit


# =============================
# MAIN FUNCTION
# =============================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.CHAT_MEMBER))

    # Jalankan task background auto kick jika bukan permanent
    asyncio.create_task(auto_kick_task(app))

    print("🤖 Bot AutoKick aktif dan memantau grup...")
    print(f"⚙️ Mode: {KICK_MODE or 'DEFAULT (10 menit)'}")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
