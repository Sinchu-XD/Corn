from telethon import events
from Bot import bot
from Database import get_file_by_id, get_channels, add_user
from bson.errors import InvalidId
from Config import Config
from telethon.tl.types import ChannelParticipant
from telethon.tl.functions.channels import GetParticipantRequest
from Decorators import subscription_required
from telethon.tl.custom import Button
import asyncio

# ✅ Function to check if user is a member of a given channel
async def is_member(client, user_id: int, channel: str) -> bool:
    try:
        chat = await client.get_entity(channel)
        result = await client(GetParticipantRequest(chat, user_id))
        participant = result.participant

        # Check participant role
        return isinstance(participant, ChannelParticipant)
    except Exception as e:
        print(f"[JOIN CHECK ERROR] {e}")
        return False

@bot.on(events.NewMessage(pattern=r"^/start\s(.+)", func=subscription_required))
async def start_link_restore(event):
    user_id = event.sender_id
    file_ref_id = event.text.split(" ", 1)[1]
    user = await event.get_sender()
    await add_user(user.id, user.first_name, user.username)

    # ✅ Enforce join for all required channels
    channels = await get_channels()
    not_joined = [ch for ch in channels if not await is_member(bot, user_id, ch)]

    if not_joined:
        await event.reply(
            "🚫 You haven't joined all required channels yet.\n"
            "Please join these channels to proceed:",
            buttons=[Button.url(ch, f"https://t.me/{ch}") for ch in not_joined]
        )
        return

    # ✅ Fetch file info
    try:
        data = await get_file_by_id(file_ref_id)
    except InvalidId:
        return await event.reply("❌ Invalid or expired file link.")

    if not data:
        return await event.reply("❌ File not found or deleted.")

    # ✅ Log activity
    try:
        await bot.send_message(
            Config.LOG_CHANNEL_ID,
            f"#RESTORE\n👤 **User:** [{user.first_name}](tg://user?id={user.id})\n"
            f"📁 **Requested File ID:** `{file_ref_id}`\n📦 **Type:** {data['file_type']}",
            parse_mode="md"
        )
    except Exception as e:
        print(f"[LOG ERROR] Failed to log restore: {e}")

    # ✅ Notify and forward media
    try:
        original_msg = await bot.get_messages(data["chat_id"], ids=data["message_id"])
        
        # Send file to user without forward tag
        sent = await bot.send_file(
            event.chat_id,
            file=original_msg.media,
            caption="📂 Sending your video...\n\nThis video will auto-delete in 20 minutes.",
            force_document=True if data["file_type"] == "document" else False
        )

        # Auto-delete the message after 20 minutes (1200 seconds)
        await asyncio.sleep(1200)
        try:
            await sent.delete()  # Delete the sent message
        except Exception as e:
            print(f"[AUTO DELETE ERROR] {e}")

    except Exception as e:
        print(f"[RESTORE ERROR] {e}")
        await event.reply("⚠️ Failed to send the file. Try again later.")

@bot.on(events.CallbackQuery(func=lambda e: e.data.decode().startswith("check_join_restore|")))
async def recheck_join_button(event):
    file_ref_id = event.data.decode().split("|")[1]
    user_id = event.sender_id
    channels = await get_channels()
    not_joined = []

    # ✅ Recheck if user has joined required channels
    for ch in channels:
        if not await is_member(bot, user_id, ch):  # Check if the user is a member
            not_joined.append(ch)

    if not_joined:
        return await event.answer("🚫 You haven't joined all required channels yet.", alert=True)

    await event.answer("✅ You're verified!", alert=True)
    await event.message.delete()

    # Simulate a /start <file_id> call again
    fake_message = event.message
    fake_message.sender_id = event.sender_id
    fake_message.text = f"/start {file_ref_id}"
    await start_link_restore(fake_message)
