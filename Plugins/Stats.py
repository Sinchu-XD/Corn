from telethon import TelegramClient, events
from Config import Config
from Database import get_users_count, files_col, channel_col, get_sudo_list
from Bot import bot

@bot.on(events.NewMessage(pattern='/stats'))
async def bot_stats(event):
    user_id = event.sender_id
    sudoers = await get_sudo_list()
    
    # Check if the user is authorized to view stats
    if user_id not in sudoers and user_id != Config.OWNER_ID:
        return await event.reply("❌ You are not authorized to view stats.")
    
    # Count stats
    total_users = await get_users_count()
    total_files = files_col.count_documents({})
    total_channels = channel_col.count_documents({})
    total_sudos = len(await get_sudo_list())
    
    # Format & send
    text = (
        "**📊 Bot Statistics**\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"📂 Total Files: `{total_files}`\n"
        f"📢 Required Channels: `{total_channels}`\n"
        f"👮‍♂️ Sudo Users: `{total_sudos}`"
    )
    await event.reply(text)
