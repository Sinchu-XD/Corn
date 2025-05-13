from telethon import TelegramClient, events, Button
from telethon.tl.types import InputPeerUser
from Config import Config
from Bot import bot
from Database import add_user, get_channels, get_sudo_list, get_main_channel
from Decorators import subscription_required, check_subscription

# ✅ Admin check
async def is_admin(uid: int) -> bool:
    sudo_users = await get_sudo_list()
    return uid == Config.OWNER_ID or uid in sudo_users

# ✅ /start command
@bot.on(events.NewMessage(pattern='/start'))
@subscription_required
async def start_command(event):
    user_id = event.sender_id
    user = await event.get_sender()
    await add_user(user.id, user.first_name, user.username)
    mention = f"[{user.first_name}](tg://user?id={user.id})"
    channels = await get_channels()  # Get all required channels
    main_channel = await get_main_channel()

    try:
        await bot.send_message(
            Config.LOG_CHANNEL_ID,
            f"#START\n👤 **User:** {mention}\n📩 Started the bot."
        )
    except Exception as e:
        print(f"Logging failed: {e}")

    # ✅ Admin view
    if await is_admin(user_id):
        if isinstance(channels, dict) and len(channels) < 2:
            return await event.reply(
                "⚠️ You need to add at least **2 channels** using:\n`/addch <slot> <@channel>`"
            )

        # Create a list of buttons for each channel
        buttons = [
            [Button.inline("📡 View Channels", b"view_channels")],
        ]
        if main_channel:
            buttons.append([Button.url("🏠 Main Channel", f"https://t.me/{main_channel}")])

        return await event.reply(
            "👋 Welcome Admin!\n\n📤 Send any file to convert into a sharable link.",
            buttons=buttons
        )

    # ✅ Normal user view
    keyboard = []

    if isinstance(channels, dict):
        # Generate buttons for each channel
        for slot, username in channels.items():
            keyboard.append([f"🔹 Slot {slot}: @{username}"])

    if main_channel:
        keyboard.append([Button.url("🏠 Main Channel", f"https://t.me/{main_channel}")])

    keyboard.append([Button.inline("✅ Check", b"check_join")])

    return await event.reply(
        "👋 To use this bot, please make sure you've joined all the required channels.\n\nOnce done, click the ✅ **Check** button below.",
        buttons=keyboard
    )


# ✅ Recheck join
@bot.on(events.CallbackQuery(pattern="check_join"))
async def recheck_subscription(event):
    user_id = event.sender_id
    if await check_subscription(bot, user_id):
        await event.edit("✅ You're successfully verified! You can now use the bot.\n\n **Please Run Same As Again You Get From Channel**")
    else:
        await event.answer("🚫 You haven't joined all channels yet.", alert=True)


# ✅ View required channels (admin only)
@bot.on(events.CallbackQuery(pattern="view_channels"))
async def view_channels_callback(event):
    user_id = event.sender_id

    if not await is_admin(user_id):
        return await event.answer("🚫 You are not allowed to view this.", alert=True)

    channels = await get_channels()
    if not channels:
        return await event.edit("❌ No channels added yet.")

    if isinstance(channels, dict):
        # If channels are stored in a dictionary, show slot details
        channel_list = "\n".join([f"🔹 Slot {slot}: @{username}" for slot, username in channels.items()])
    elif isinstance(channels, list):
        # If channels are stored in a list, show channel names
        channel_list = "\n".join([f"🔹 @{username}" for username in channels])
    else:
        return await event.edit("⚠️ Invalid channel data format.")

    await event.edit(
        f"📡 **Required Channels:**\n\n{channel_list}",
        buttons=[Button.inline("🔙 Back", b"start_back")]
    )


# ✅ Back to admin start view
@bot.on(events.CallbackQuery(pattern="start_back"))
async def back_to_start(event):
    user_id = event.sender_id
    if not await is_admin(user_id):
        return await event.answer("🚫 Not allowed.", alert=True)

    main_channel = await get_main_channel()
    buttons = [Button.inline("📡 View Channels", b"view_channels")]
    if main_channel:
        buttons.append(Button.url("🏠 Main Channel", f"https://t.me/{main_channel}"))

    await event.edit(
        "👋 Welcome Admin!\n\n📤 Send any file to convert into a sharable link.",
        buttons=buttons
    )
    
