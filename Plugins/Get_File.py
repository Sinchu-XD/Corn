from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from Bot import bot
from Database import get_file_by_id
from Config import Config
from bson.errors import InvalidId
import asyncio


# ✅ Function to check if user is a member of a given channel
async def is_member(client: Client, user_id: int, channel: str) -> bool:
    try:
        member = await client.get_chat_member(channel, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


@bot.on_message(filters.command("start") & filters.private & filters.regex(r"^/start\s(.+)"))
async def start_link_restore(c: Client, m: Message):
    user_id = m.from_user.id
    file_ref_id = m.text.split(" ", 1)[1]

    # ✅ Enforce join for both required channels
    required_channels = ["StreeCorporation", "StreeHub"]
    not_joined = []

    for ch in required_channels:
        if not await is_member(c, user_id, ch):
            not_joined.append(ch)

    if not_joined:
        buttons = [
            [InlineKeyboardButton(f"📡 Join @{ch}", url=f"https://t.me/{ch}")] for ch in not_joined
        ]
        buttons.append([InlineKeyboardButton("✅ I Joined", callback_data=f"check_join_restore|{file_ref_id}")])
        return await m.reply(
            "🚫 To access the file, please join the required channels first:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # ✅ Proceed with file restore
    try:
        data = await get_file_by_id(file_ref_id)
    except InvalidId:
        return await m.reply("❌ Invalid or expired file link.")

    if not data:
        return await m.reply("❌ File not found or deleted.")

    # ✅ Log restore activity
    try:
        await bot.send_message(
            Config.LOG_CHANNEL_ID,
            f"#RESTORE\n👤 **User:** {m.from_user.mention}\n"
            f"📁 **Requested File ID:** `{file_ref_id}`\n📦 **Type:** {data['file_type']}"
        )
    except Exception as e:
        print(f"[LOG ERROR] Failed to log restore: {e}")

    # Send info
    info_msg = await m.reply(
        f"**📂 Sending your {data['file_type']}...**\n\nThis {data['file_type']} will auto-delete in 20 minutes.",
        quote=True
    )

    # Send media
    sent = await c.send_cached_media(m.chat.id, data["file_id"])

    # ⏳ Auto-delete after 20 minutes
    await asyncio.sleep(1200)
    try:
        await sent.delete()
        await info_msg.delete()
    except Exception as e:
        print(f"[AUTO DELETE ERROR] {e}")

from pyrogram.types import CallbackQuery

@bot.on_callback_query(filters.regex(r"check_join_restore\|(.+)"))
async def recheck_restore_join(c: Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    file_ref_id = cb.data.split("|")[1]

    required_channels = ["StreeCorporation", "StreeHub"]
    not_joined = []

    for ch in required_channels:
        if not await is_member(c, user_id, ch):
            not_joined.append(ch)

    if not_joined:
        return await cb.answer("🚫 You haven't joined all required channels yet.", show_alert=True)

    # User has now joined — trigger file restore again
    await cb.message.delete()
    fake_message = cb.message
    fake_message.text = f"/start {file_ref_id}"
    await start_link_restore(c, fake_message)
