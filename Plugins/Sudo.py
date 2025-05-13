from telethon import TelegramClient, events
from Config import Config
from Bot import bot
from Database import add_sudo, remove_sudo, get_sudo_list
from Decorators import owner_only
from telethon.errors import UsernameNotOccupiedError, UserNotParticipantError

@bot.on(events.NewMessage(pattern="/addsudo(?:\s+(.+))?", func=owner_only))
async def add_sudo_user(event):
    # Extract the user ID or username from the command
    input_data = event.pattern_match.group(1)  # This gets the user_id or username

    if not input_data:
        return await event.reply("Please provide a user ID or username.")

    try:
        if input_data.isdigit():  # Check if input is a user ID (numeric)
            user_id = int(input_data)
        else:  # If not, it's assumed to be a username
            user = await bot.get_entity(input_data)
            user_id = user.id
    except (ValueError, UsernameNotOccupiedError, UserNotParticipantError) as e:
        return await event.reply(f"❌ Failed to find user: {e}")

    # Add the user as sudo
    await add_sudo(user_id)
    await event.reply(f"✅ Added `{user_id}` to Sudo Users.")

@bot.on(events.NewMessage(pattern="/remsudo(?:\s+(.+))?", func=owner_only))
async def remove_sudo_user(event):
    # Extract the user ID or username from the command
    input_data = event.pattern_match.group(1)  # This gets the user_id or username

    if not input_data:
        return await event.reply("Please provide a user ID or username.")

    try:
        if input_data.isdigit():  # Check if input is a user ID (numeric)
            user_id = int(input_data)
        else:  # If not, it's assumed to be a username
            user = await bot.get_entity(input_data)
            user_id = user.id
    except (ValueError, UsernameNotOccupiedError, UserNotParticipantError) as e:
        return await event.reply(f"❌ Failed to find user: {e}")

    # Remove the user from sudo
    await remove_sudo(user_id)
    await event.reply(f"❌ Removed `{user_id}` from Sudo Users.")

@bot.on(events.NewMessage(pattern="/sudolist", func=owner_only))
async def sudo_list(event):
    sudoers = await get_sudo_list()
    if not sudoers:
        return await event.reply("No Sudo Users added.")
    
    msg = "**🔰 Sudo Users List:**\n"
    msg += "\n".join([f"- `{x}`" for x in sudoers])
    await event.reply(msg)
