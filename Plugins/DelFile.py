from telethon import events
from bson import ObjectId
from bson.errors import InvalidId
from Bot import bot
from Database import files_col, get_sudo_list
from Config import Config


async def is_authorized(user_id: int) -> bool:
    sudoers = await get_sudo_list()
    return user_id in sudoers or user_id == Config.OWNER_ID


@bot.on(events.NewMessage(pattern=r"/delfile(?:\s+(.+))?"))
async def delete_file_handler(event: events.NewMessage.Event):
    sender = await event.get_sender()
    user_id = sender.id

    if not await is_authorized(user_id):
        return await event.reply("❌ You don't have permission to use this command.")

    file_id = event.pattern_match.group(1)
    if not file_id:
        return await event.reply("Usage:\n`/delfile <file_id>`")

    try:
        result = files_col.delete_one({"_id": ObjectId(file_id)})
        if result.deleted_count:
            return await event.reply("✅ File deleted successfully.")
        else:
            return await event.reply("❌ No file found with that ID.")
    except InvalidId:
        return await event.reply("❌ Invalid file ID format.")


@bot.on(events.NewMessage(pattern="/delallfiles"))
async def delete_all_files_handler(event: events.NewMessage.Event):
    sender = await event.get_sender()
    user_id = sender.id

    if not await is_authorized(user_id):
        return await event.reply("❌ You don't have permission to use this command.")

    result = files_col.delete_many({})
    await event.reply(f"✅ Deleted `{result.deleted_count}` files from the database.")
