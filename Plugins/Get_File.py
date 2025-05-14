from telethon import events
from Bot import bot
from Database import get_file_by_id, get_channels, add_user
from bson.errors import InvalidId
from Config import Config
from telethon.errors import UserNotParticipantError, ChatAdminRequiredError
from telethon.tl.functions.channels import GetParticipantRequest
from Decorators import subscription_required, check_subscription
from telethon.tl.custom import Button
import asyncio

# ✅ Function to check if the user is subscribed to all required channels
# ✅ /start <file_id> handler
@bot.on(events.NewMessage(pattern=r"^/start\s(.+)", func=subscription_required))
async def start_link_restore(event):
    user_id = event.sender_id
    file_ref_id = event.text.split(" ", 1)[1]
    user = await event.get_sender()
    await add_user(user.id, user.first_name, user.username)

    is_subscribed = await check_subscription(bot, user_id)

    if not is_subscribed:
        channels = await get_channels()
        buttons = [
            [Button.url("Join " + ch, f"https://t.me/{ch}") for ch in (channels.values() if isinstance(channels, dict) else channels)],
            [Button.inline("✅ I've Joined", data=f"check_join_restore|{file_ref_id}")]
        ]
        await event.reply(
            "🚫 You haven't joined all required channels yet.\nPlease join them to continue.",
            buttons=buttons
        )
        return

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

# ✅ Callback Query to recheck join status
@bot.on(events.CallbackQuery(func=lambda e: e.data.decode().startswith("check_join_restore|")))
async def recheck_join_button(event):
    file_ref_id = event.data.decode().split("|")[1]
    user_id = event.sender_id

    if not await check_subscription(bot, user_id):
        await event.reply("🚫 You haven't joined all required channels yet.\n")
        return

    await event.answer("✅ You're verified!", alert=True)
    await event._message.delete()

    # Fake /start <file_id> trigger
    class FakeEvent:
        def __init__(self, message, user_id):
            self.message = message
            self.chat_id = message.chat_id
            self.sender_id = user_id
            self.text = message.text

        async def get_sender(self):
            return await bot.get_entity(user_id)

    fake_event = FakeEvent(event.message, user_id)
    fake_event.text = f"/start {file_ref_id}"
    await start_link_restore(fake_event)
    
