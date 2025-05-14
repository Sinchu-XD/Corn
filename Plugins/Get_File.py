from telethon import events
from Bot import bot
from Decorators import subscription_required
from Database import get_file_by_id, add_user
from bson.errors import InvalidId
from Config import Config
import asyncio

# ✅ /start <file_id> handler without channel checks
@bot.on(events.NewMessage(pattern=r"^/start\s(.+)"))
@subscription_required
async def start_link_restore(event):
    user_id = event.sender_id
    file_ref_id = event.text.split(" ", 1)[1]
    user = await event.get_sender()
    await add_user(user.id, user.first_name, user.username)

    try:
        data = await get_file_by_id(file_ref_id)
    except InvalidId:
        return await event.reply("❌ Invalid or expired file link.")

    if not data:
        return await event.reply("❌ File not found or deleted.")

    try:
        await bot.send_message(
            Config.LOG_CHANNEL_ID,
            f"#RESTORE\n👤 **User:** [{user.first_name}](tg://user?id={user.id})\n"
            f"📁 **Requested File ID:** `{file_ref_id}`\n📦 **Type:** {data['file_type']}",
            parse_mode="md"
        )
    except Exception as e:
        print(f"[LOG ERROR] {e}")

    try:
        original_msg = await bot.get_messages(data["chat_id"], ids=data["message_id"])
        sent = await bot.send_file(
            event.chat_id,
            file=original_msg.media,
            caption="📂 Sending your video...\n\nThis video will auto-delete in 20 minutes.",
            force_document=(data["file_type"] == "document")
        )
        await asyncio.sleep(1200)
        try:
            await sent.delete()
        except Exception as e:
            print(f"[AUTO DELETE ERROR] {e}")
    except Exception as e:
        print(f"[RESTORE ERROR] {e}")
        await event.reply("⚠️ Failed to send the file. Try again later.")

