from telethon import events
from Bot import bot
from Config import Config
from Database import get_all_users, get_sudo_list
import asyncio

async def is_admin(uid: int) -> bool:
    sudo_users = await get_sudo_list()
    return uid == Config.OWNER_ID or uid in sudo_users

@bot.on(events.NewMessage(pattern="/broadcast"))
async def broadcast_handler(event):
    sender = event.sender_id

    if not await is_admin(sender):
        return await event.reply("❌ You are not authorized to use this command.")

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        return await event.reply("❌ Please reply to a message (text/photo/video) to broadcast.")

    users = await get_all_users()
    total = len(users)
    done = 0
    failed = 0

    status_msg = await event.reply(f"📢 Starting broadcast to {total} users...")

    for uid in users:
        try:
            if reply_msg.media:
                await bot.send_file(
                    uid,
                    file=reply_msg.media,
                    caption=reply_msg.text or "",
                    force_document=False,
                    parse_mode='md'
                )
            elif reply_msg.text:
                await bot.send_message(uid, reply_msg.text, parse_mode='md')
            done += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.1)  # prevent flood wait

    await status_msg.edit(
        f"✅ **Broadcast finished**\n\n👥 Total: {total}\n✅ Sent: {done}\n❌ Failed: {failed}"
    )
  
