from pyrogram import Client, filters
from Bot import bot
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Config import Config
from Decorators import check_user_joined
from Database import get_channels, get_sudo_list
from datetime import datetime

@bot.on_message(filters.command("start"))
async def start_bot(client: Client, message: Message):
    user_id = message.from_user.id
    mention = message.from_user.mention
    channels = await get_channels()
    sudoers = await get_sudo_list()

    # Log start
    try:
        await client.send_message(
            Config.LOG_GROUP_ID,
            f"👤 User : {mention} started the bot.\n🕒 `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        )
    except:
        pass

    # No channels configured
    if not channels or len(channels) < 2:
        if user_id == Config.OWNER_ID or user_id in sudoers:
            return await message.reply("⚠️ Add at least 2 channels using `/addchannel` to make the bot functional.")
        return await message.reply("⚠️ Bot is under setup. Please wait until the owner configures it.")

    # Check if user joined all required channels
    joined = await check_user_joined(client, user_id)
    if not joined:
        buttons = [[InlineKeyboardButton("✅ I've Joined All", callback_data="check_join")]]
        for ch in channels:
            buttons.insert(0, [InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch.replace('@', '')}")])
        return await message.reply(
            "**🔒 Please join all the required channels to use the bot.**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # If joined and non-owner/sudo, only show thank you
    if user_id != Config.OWNER_ID and user_id not in sudoers:
        return await message.reply("✅ **Thanks for joining us!**")

    # If sudo/owner
    await message.reply(
        "✅ You're verified!\n\nNow send me a **File** (Photo, Video, or Document) to get a direct link.",
    )


@bot.on_callback_query(filters.regex("check_join"))
async def recheck_join(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    joined = await check_user_joined(client, user_id)
    if not joined:
        return await callback_query.answer("❌ You still haven't joined all channels!", show_alert=True)

    sudoers = await get_sudo_list()

    # Show message based on user type
    if user_id != Config.OWNER_ID and user_id not in sudoers:
        return await callback_query.message.edit_text("✅ **Thanks for joining us!**")

    await callback_query.message.edit_text(
        "✅ You're verified!\n\nNow send me a **File** (Photo, Video, or Document) to get a direct link."
    )
