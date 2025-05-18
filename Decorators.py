from Config import Config
from Bot import bot
from telethon import events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError, ChatAdminRequiredError
from Database import get_channels, get_sudo_list, get_main_channel, get_file_by_id
from functools import wraps
import asyncio

# ✅ Check if the user is subscribed to all required channels
async def check_subscription(client, user_id: int) -> bool:
    channels = await get_channels()
    if not channels:
        return True

    usernames = list(channels.values()) if isinstance(channels, dict) else channels

    for channel in usernames:
        try:
            result = await client(GetParticipantRequest(channel, user_id))
            if result.participant is None:
                return False
        except UserNotParticipantError:
            return False
        except ChatAdminRequiredError:
            # Bot might not be admin, skip this channel
            continue
        except Exception as e:
            print(f"[Subscription Check Error] {e}")
            continue

    return True

# ✅ Send file based on file_ref_id using your DB and Telegram message media
async def send_file_by_ref_id(event, file_ref_id: str):
    data = await get_file_by_id(file_ref_id)
    if not data:
        await event.respond("❌ File not found or deleted.")
        return

    try:
        # Fetch the original Telegram message containing the media
        original_msg = await bot.get_messages(data["chat_id"], ids=data["message_id"])

        sent = await event.client.send_file(
            event.chat_id,
            file=original_msg.media,
            caption="📂 Sending your video...\n\nThis video will auto-delete in 20 minutes.",
            force_document=(data["file_type"] == "document"),
            has_protected_content=True
        )

        # Auto-delete after 20 minutes (1200 seconds)
        await asyncio.sleep(1200)
        try:
            await sent.delete()
        except Exception as e:
            print(f"[Auto-delete error] {e}")

    except Exception as e:
        print(f"[File Send Error] {e}")
        await event.respond("⚠️ Failed to send the file. Try again later.")

# ✅ Subscription Required Decorator
def subscription_required(func):
    @wraps(func)
    async def wrapper(event: events.NewMessage.Event):
        user_id = event.sender_id
        if await check_subscription(event.client, user_id):
            return await func(event)

        channels = await get_channels()
        main_channel = await get_main_channel()
        buttons = []

        usernames = list(channels.values()) if isinstance(channels, dict) else channels
        for username in usernames:
            buttons.append([Button.url(f"📡 Join @{username}", f"https://t.me/{username}")])

        file_ref_id = None
        if event.text and event.text.startswith("/start "):
            file_ref_id = event.text.split(" ", 1)[1]

        buttons.append([Button.inline("✅ I Joined", data=f"check_join_{file_ref_id or 'none'}".encode())])

        await event.respond(
            "📥 Please join all required channels to use this bot:",
            buttons=buttons
        )
    return wrapper

# ✅ Callback for "✅ I Joined" Button
@bot.on(events.CallbackQuery(pattern=b"check_join_(.+)"))
async def recheck_subscription(event):
    user_id = event.sender_id
    data_str = event.data.decode()
    parts = data_str.split("_", 2)
    file_ref_id = parts[2] if len(parts) > 2 else None

    main_channel = await get_main_channel()

    keyboard = []
    if main_channel:
        keyboard.append([Button.url("🏠 Main Channel", f"https://t.me/{main_channel}")])

    if await check_subscription(bot, user_id):
        await event.edit(
            """
• You're Successfully Verified.
• Now You Can Use Bot Without Any Interrupt.
• Please Click On Main Channel For All 18+ Contents.
• You Get Many Videos There, Only You Have To Click On Link Which One You Want.

• आपका सफलतापूर्वक सत्यापन हो गया है।
• अब आप बिना किसी रुकावट के बॉट का उपयोग कर सकते हैं।
• कृपया सभी 18+ वीडियो के लिए Main Channel पर क्लिक करें |
• आपको वहां कई वीडियो मिलेंगे, आपको उस लिंक पर क्लिक करना है जो आप देखना चाहते हैं |
👇🏻👇🏻👇🏻
            """,
            buttons=keyboard
        )

        if file_ref_id and file_ref_id != "none":
            try:
                await send_file_by_ref_id(event, file_ref_id)
            except Exception as e:
                await event.respond(f"Error sending file: {e}")

    else:
        await event.answer("🚫 You haven't joined all channels yet.", alert=True)

    try:
        if hasattr(event, '_message') and event._message:
            await event._message.delete()
    except Exception as e:
        print(f"[Message Delete Error] {e}")


async def delete_messages(user_message, bot_message, delay=5):
    await asyncio.sleep(delay)
    try:
        await user_message.delete()
    except:
        pass
    try:
        await bot_message.delete()
    except:
        pass



# ✅ Admin/Sudo Checks
def owner_only(event: events.NewMessage.Event):
    return event.sender_id == Config.OWNER_ID

async def is_sudo(event: events.NewMessage.Event):
    sudoers = await get_sudo_list()
    return event.sender_id in sudoers

async def owner_or_sudo(event):
    user = await event.get_sender()
    sudoers = await get_sudo_list()
    return user and (user.id in sudoers or user.id == Config.OWNER_ID)
    
