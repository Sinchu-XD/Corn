# helpers/filters.py

from pyrogram import filters
from Config import Config

def owner_only(_, __, m):
    return m.from_user and m.from_user.id == Config.OWNER_ID

owner_only = filters.create(owner_only)

# Add below owner_only in helpers/filters.py

from Database import get_sudo_list

async def is_sudo(_, __, m):
    sudoers = await get_sudo_list()
    return m.from_user and m.from_user.id in sudoers

sudo_only = filters.create(is_sudo)

owner_or_sudo = owner_only | sudo_only

# helpers/check_join.py

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import UserNotParticipant, PeerIdInvalid
from pyrogram.enums import ChatMemberStatus
from functools import wraps
from Database import get_channels, get_force_check, get_sudo_list
from Config import Config

async def check_subscription(client, user_id: int) -> bool:
    channels = await get_channels()
    if not channels:
        return True  # No channels to check

    usernames = []
    if isinstance(channels, dict):
        usernames = list(channels.values())
    elif isinstance(channels, list):
        usernames = channels

    for channel in usernames:
        try:
            member = await client.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ("kicked", "left"):
                return False
        except UserNotParticipant:
            return False
        except Exception as e:
            print(f"[Subscription Check Error] {e}")
            continue  # Skip problematic channels

    return True

from functools import wraps
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from .Database import get_channels, get_main_channel
from .Config import Config
from .Decorators import check_subscription

def subscription_required(func):
    @wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        user_id = message.from_user.id
        if await check_subscription(client, user_id):
            return await func(client, message, *args, **kwargs)

        channels = await get_channels()
        main_channel = await get_main_channel()
        keyboard = []

        if isinstance(channels, dict):
            for slot, username in channels.items():
                keyboard.append([InlineKeyboardButton(f"📡 Join @{username}", url=f"https://t.me/{username}")])
        elif isinstance(channels, list):
            for username in channels:
                keyboard.append([InlineKeyboardButton(f"📡 Join @{username}", url=f"https://t.me/{username}")])

        keyboard.append([InlineKeyboardButton("✅ I Joined", callback_data="check_join")])
        if main_channel:
            keyboard.append([InlineKeyboardButton("🏠 Main Channel", url=f"https://t.me/{main_channel}")])

        return await message.reply(
            "📥 Please join all required channels to use this bot:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    return wrapper
