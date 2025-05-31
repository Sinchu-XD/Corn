import time
from collections import defaultdict
from telethon import events, Button
from telethon.errors import UserIsBlockedError, ChatWriteForbiddenError
from Config import Config
from Bot import bot
from Database import add_user, get_sudo_list
from Database import add_blocked_user, get_blocked_user, remove_blocked_user

# Spam protection
user_command_times = defaultdict(list)
VIOLATION_WINDOW = 5  # seconds
BLOCK_DURATION = 10 * 60  # 20 minutes

# ✅ Admin check
async def is_admin(uid: int) -> bool:
    sudo_users = await get_sudo_list()
    return uid == Config.OWNER_ID or uid in sudo_users

# ✅ /start command
@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    user_id = event.sender_id
    user = await event.get_sender()
    now = time.time()

    # ✅ Check if user is blocked in DB
    unblock_time = await get_blocked_user(user_id)
    if unblock_time:
        if now >= unblock_time:
            await remove_blocked_user(user_id)
            user_command_times[user_id].clear()
            try:
                await bot.send_message(
                    user_id,
                    "**✅ You are now unblocked. Please avoid spamming commands**.\n\n"
                    "**✅ अब आप अनब्लॉक हो चुके हैं। कृपया बार-बार कमांड भेजना बंद करें।**"
                )
            except:
                pass
        else:
            wait = int((unblock_time - now) / 60)
            await event.reply(
                f"**⛔ You are blocked for {wait} more minutes due to spamming.**\n\n"
                f"**⛔ आप {wait} मिनट के लिए ब्लॉक हैं क्योंकि आपने बार-बार कमांड भेजी।**"
            )
            return

    # ✅ Track command timestamps
    user_command_times[user_id].append(now)
    user_command_times[user_id] = [
        t for t in user_command_times[user_id] if now - t <= VIOLATION_WINDOW
    ]

    if len(user_command_times[user_id]) == 3:
        await event.reply(
            "⚠️ **Stop spamming commands! One more and you will be blocked for 10 minutes.**\n\n"
            "⚠️ **बार-बार कमांड मत भेजो! अगली बार 10 मिनट के लिए ब्लॉक हो जाओगे।**"
        )
    elif len(user_command_times[user_id]) > 3:
        await add_blocked_user(user_id, BLOCK_DURATION)
        user_command_times[user_id].clear()
        await event.reply(
            "⛔ **You are now blocked for 10 minutes due to spamming.**\n\n"
            "⛔ **आप 10 मिनट के लिए ब्लॉक हो चुके हैं क्योंकि आपने बार-बार कमांड भेजी।**"
        )

        # ✅ Log to LOG_CHANNEL
        mention = f"[{user.first_name}](tg://user?id={user.id})"
        try:
            await bot.send_message(
                Config.LOG_CHANNEL_ID,
                f"🚫 #BLOCKED\n👤 **User:** {mention} (`{user.id}`)\n📛 Reason: Spammed `/start` more than 3 times in {VIOLATION_WINDOW} seconds.",
                parse_mode='md'
            )
        except:
            pass
        return

    # ✅ Add user to DB
    await add_user(user.id, user.first_name, user.username)
    mention = f"[{user.first_name}](tg://user?id={user.id})"

    # ✅ Log user start
    try:
        await bot.send_message(
            Config.LOG_CHANNEL_ID,
            f"#START\n👤 **User:** {mention}\n📩 Started the bot.",
            parse_mode='md'
        )
    except (UserIsBlockedError, ChatWriteForbiddenError, Exception):
        pass

    # ✅ Buttons
    keyboard = [
        [Button.url("🏠 Main Channel", "https://t.me/StreeHub")],
        [Button.url("How To Use Bot", "https://t.me/SexyStreeBot/6")]
    ]

    if await is_admin(user_id):
        return await event.reply(
            "👋 Welcome Admin!\n\n📤 Send any file to convert into a sharable link."
        )

    return await event.reply(
        "•  **How To Use Bot Tutorial Watch Here :-**\n\n"
        "• **बॉट ट्यूटोरियल का उपयोग कैसे करें यहां क्लिक करके देखें:**\n👇🏻👇🏻👇🏻",
        buttons=keyboard
    )
