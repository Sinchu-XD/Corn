from Config import Config
from Bot import bot
from telethon import events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError, ChatAdminRequiredError
from Database import get_channels, get_sudo_list, get_main_channel
from functools import wraps

# Check if the user is subscribed to all required channels
async def check_subscription(client, user_id: int) -> bool:
    channels = await get_channels()
    if not channels:
        return True  # No channels to check, considered as subscribed

    usernames = list(channels.values()) if isinstance(channels, dict) else channels

    for channel in usernames:
        try:
            result = await client(GetParticipantRequest(channel, user_id))
            # If the user is banned, return False
            if result.participant is None:  # Participant doesn't exist or is banned
                return False
        except UserNotParticipantError:
            return False  # User is not a participant
        except ChatAdminRequiredError:
            continue  # Skip if bot can't access participant details
        except Exception as e:
            print(f"[Subscription Check Error] {e}")
            continue  # Continue checking other channels

    return True  # User is subscribed to all channels

# Decorator to enforce subscription requirement
def subscription_required(func):
    @wraps(func)
    async def wrapper(event: events.NewMessage.Event):
        user_id = event.sender_id
        if await check_subscription(event.client, user_id):
            return await func(event)

        # If not subscribed, show a subscription reminder with buttons
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
        return
    return wrapper

from telethon import Button
from telethon.tl.functions.messages import DeleteMessagesRequest

@bot.on(events.CallbackQuery(pattern="check_join"))
async def recheck_subscription(event):
    user_id = event.sender_id
    if await check_subscription(bot, user_id):
        await event.edit("✅ You're successfully verified! You can now use the bot.\n\n **Please Run Same As Again You Get From Channel**")
    else:
        await event.answer("🚫 You haven't joined all channels yet.", alert=True)

    # Check if event._message exists before trying to delete it
    if event._message:
        try:
            await event._message.delete()
        except Exception as e:
            print(f"Failed to delete the message: {e}")
        
# Function to check if the user is the owner of the bot
def owner_only(event: events.NewMessage.Event):
    return event.sender_id == Config.OWNER_ID

# Function to check if the user is in the sudo list
async def is_sudo(event: events.NewMessage.Event):
    sudoers = await get_sudo_list()
    return event.sender_id in sudoers

# Function to check if the user is either the owner or a sudo user
async def owner_or_sudo(event):
    user = await event.get_sender()
    sudoers = await get_sudo_list()
    return user and (user.id in sudoers or user.id == Config.OWNER_ID)
