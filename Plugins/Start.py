from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Bot import bot
from Config import Config
from Decorators import subscription_required, check_subscription
from Database import get_channels, get_sudo_list, get_main_channel


# ✅ Admin check
async def is_admin(uid: int) -> bool:
    sudo_users = await get_sudo_list()
    return uid == Config.OWNER_ID or uid in sudo_users


# ✅ /start command
@bot.on_message(filters.command("start"))
@subscription_required
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    mention = message.from_user.mention
    channels = await get_channels()
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
            return await message.reply(
                "⚠️ You need to add at least **2 channels** using:\n`/addch <slot> <@channel>`"
            )

        buttons = [[InlineKeyboardButton("📡 View Channels", callback_data="view_channels")]]
        if main_channel:
            buttons.append([InlineKeyboardButton("🏠 Main Channel", url=f"https://t.me/{main_channel}")])

        return await message.reply(
            "👋 Welcome Admin!\n\n📤 Send any file to convert into a sharable link.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # ✅ Normal user view
    keyboard = []

    if main_channel:
        keyboard.append([InlineKeyboardButton("🏠 Main Channel", url=f"https://t.me/{main_channel}")])

    keyboard.append([InlineKeyboardButton("✅ Check", callback_data="check_join")])

    return await message.reply(
        "👋 To use this bot, please make sure you've joined all the required channels.\n\nOnce done, click the ✅ **Check** button below.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ✅ Recheck join
@bot.on_callback_query(filters.regex("check_join"))
async def recheck_subscription(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if await check_subscription(client, user_id):
        await callback_query.message.edit("✅ You're successfully verified! You can now use the bot.")
    else:
        await callback_query.answer("🚫 You haven't joined all channels yet.", show_alert=True)


# ✅ View required channels (admin only)
@bot.on_callback_query(filters.regex("view_channels"))
async def view_channels_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if not await is_admin(user_id):
        return await callback_query.answer("🚫 You are not allowed to view this.", show_alert=True)

    channels = await get_channels()
    if not channels:
        return await callback_query.message.edit("❌ No channels added yet.")

    if isinstance(channels, dict):
        channel_list = "\n".join([f"🔹 Slot {slot}: @{username}" for slot, username in channels.items()])
    elif isinstance(channels, list):
        channel_list = "\n".join([f"🔹 @{username}" for username in channels])
    else:
        return await callback_query.message.edit("⚠️ Invalid channel data format.")

    await callback_query.message.edit(
        f"📡 **Required Channels:**\n\n{channel_list}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="start_back")]
        ])
    )


# ✅ Back to admin start view
@bot.on_callback_query(filters.regex("start_back"))
async def back_to_start(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if not await is_admin(user_id):
        return await callback_query.answer("🚫 Not allowed.", show_alert=True)

    main_channel = await get_main_channel()
    buttons = [[InlineKeyboardButton("📡 View Channels", callback_data="view_channels")]]
    if main_channel:
        buttons.append([InlineKeyboardButton("🏠 Main Channel", url=f"https://t.me/{main_channel}")])

    await callback_query.message.edit(
        "👋 Welcome Admin!\n\n📤 Send any file to convert into a sharable link.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
