import time
from collections import defaultdict
from telethon import events
from Bot import bot as app

# Constants
VIOLATION_WINDOW = 7  # Seconds
BLOCK_DURATION = 20 * 60  # 20 minutes

# Trackers
user_command_times = defaultdict(list)
blocked_users = {}

def is_user_blocked(user_id):
    if user_id in blocked_users:
        if time.time() < blocked_users[user_id]:
            return True
        else:
            del blocked_users[user_id]
    return False

@app.on(events.NewMessage(pattern=r'^/'))
async def command_protection(event):
    if not event.is_private:
        return

    user_id = event.sender_id

    # If user is blocked
    if is_user_blocked(user_id):
        return await event.reply(
            "⛔ You are temporarily blocked for spamming commands.\n"
            "⛔ आप कमांड स्पैम करने के कारण अस्थायी रूप से ब्लॉक हैं। 20 मिनट बाद दोबारा कोशिश करें।"
        )

    # Track command timestamps
    now = time.time()
    user_command_times[user_id].append(now)
    user_command_times[user_id] = [
        t for t in user_command_times[user_id] if now - t <= VIOLATION_WINDOW
    ]

    # Respond based on how many commands sent in time window
    if len(user_command_times[user_id]) == 3:
        await event.reply(
            "⚠️ Please do not spam commands! You will be blocked if you continue.\n"
            "⚠️ कृपया कमांड स्पैम न करें! अगर फिर किया तो ब्लॉक कर दिए जाओगे।"
        )
    elif len(user_command_times[user_id]) >= 5:
        blocked_users[user_id] = now + BLOCK_DURATION
        user_command_times[user_id].clear()
        return await event.reply(
            "⛔ You’ve been blocked for 20 minutes due to repeated spamming.\n"
            "⛔ बार-बार स्पैम करने के कारण आपको 20 मिनट के लिए ब्लॉक कर दिया गया है।"
        )
