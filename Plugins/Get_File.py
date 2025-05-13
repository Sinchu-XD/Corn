from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from Bot import bot
from Database import get_file_by_id, get_channels, add_user
from bson.errors import InvalidId
from Decorators import subscription_required, check_subscription
from Config import Config
from bson.errors import InvalidId
import asyncio


# ✅ Function to check if user is a member of a given channel
async def is_member(client: Client, user_id: int, channel: str) -> bool:
    try:
        chat = await client.get_chat(channel)
        member = await client.get_chat_member(chat.id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"[JOIN CHECK ERROR] {e}")
        return False

@bot.on_message(filters.command("start") & filters.private & filters.regex(r"^/start\s(.+)"))
@subscription_required
async def start_link_restore(c: Client, m: Message):
    user_id = m.from_user.id
    file_ref_id = m.text.split(" ", 1)[1]
    user = m.from_user
    await add_user(user.id, user.first_name, user.username)
    

    # ✅ Enforce join for both required channels


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
async def recheck_join_button(c: Client, cb: CallbackQuery):
    file_ref_id = cb.data.split("|")[1]
    user_id = cb.from_user.id
    channels = await get_channels()
    not_joined = []

    for ch in channels:
        if not await check_subscription(c, user_id):
            not_joined.append(ch)

    if not_joined:
        return await cb.answer("🚫 You haven't joined all required channels yet.", show_alert=True)

    await cb.answer("✅ You're verified!", show_alert=True)
    await cb.message.delete()

    # Simulate a /start <file_id> call again
    fake_message = cb.message
    fake_message.from_user = cb.from_user
    fake_message.text = f"/start {file_ref_id}"
    await start_link_restore(c, fake_message)
