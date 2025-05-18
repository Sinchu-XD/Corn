import time
import asyncio
from telethon import events
from Bot import bot as app
from Decorators import delete_messages

COMMAND_COOLDOWN = 3
user_last_command = {}
enabled_users = set()

def is_spam_allowed(user_id):
    now = time.time()
    last_time = user_last_command.get(user_id, 0)
    if now - last_time < COMMAND_COOLDOWN:
        return False
    user_last_command[user_id] = now
    return True

@app.on(events.NewMessage(pattern=r'^/spam_on$'))
async def enable_spam_protection(event):
    if not event.is_private:
        return
    user_id = event.sender_id
    enabled_users.add(user_id)
    m = await event.respond("✅ Spam protection has been enabled for you.")
    asyncio.create_task(delete_messages(event.message, m))

@app.on(events.NewMessage(pattern=r'^/spam_off$'))
async def disable_spam_protection(event):
    if not event.is_private:
        return
    user_id = event.sender_id
    enabled_users.discard(user_id)
    m = await event.respond("❎ Spam protection has been disabled for you.")
    asyncio.create_task(delete_messages(event.message, m))
