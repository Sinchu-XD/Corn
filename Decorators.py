from Config import Config
from Bot import bot
from telethon import events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError, ChatAdminRequiredError
from Database import get_channels, get_sudo_list, get_main_channel
from functools import wraps

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
            continue
        except Exception as e:
            print(f"[Subscription Check Error] {e}")
            continue

    return True

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

        if main_channel:
            buttons.append([Button.url("🏠 Main Channel", f"https://t.me/{main_channel}")])

        buttons.append([Button.inline("✅ I Joined", b"check_join")])

        await event.respond(
            "📥 Please join all required channels to use this bot:",
            buttons=buttons
        )
    return wrapper

# ✅ Callback for "✅ I Joined" Button
@bot.on(events.CallbackQuery(pattern="check_join"))
async def recheck_subscription(event):
    user_id = event.sender_id
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
    else:
        await event.answer("🚫 You haven't joined all channels yet.", alert=True)

    # ✅ Safely delete the previous message if available
    try:
        if hasattr(event, '_message') and event._message:
            await event._message.delete()
    except Exception as e:
        print(f"[Message Delete Error] {e}")

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
    
