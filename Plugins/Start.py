from telethon import TelegramClient, events, Button
from telethon.tl.types import InputPeerUser
from Config import Config
from Bot import bot
from Database import add_user, get_sudo_list, get_main_channel
from Decorators import subscription_required

# ✅ Admin check
async def is_admin(uid: int) -> bool:
    sudo_users = await get_sudo_list()
    return uid == Config.OWNER_ID or uid in sudo_users

# ✅ /start command without any channel logic
@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    user_id = event.sender_id
    user = await event.get_sender()
    await add_user(user.id, user.first_name, user.username)
    mention = f"[{user.first_name}](tg://user?id={user.id})"

    try:
        await bot.send_message(
            Config.LOG_CHANNEL_ID,
            f"#START\n👤 **User:** {mention}\n📩 Started the bot."
        )
    except Exception as e:
        print(f"Logging failed: {e}")

    main_channel = await get_main_channel()

    keyboard = []
    if main_channel:
        keyboard.append([Button.url("🏠 Main Channel", f"https://t.me/{main_channel}")])

    # ✅ Admin view
    if await is_admin(user_id):
        return await event.reply(
            "👋 Welcome Admin!\n\n📤 Send any file to convert into a sharable link."
        )

    # ✅ Normal user view (no channel check, no subscription check)
    return await event.reply(
        "•  Now You Can Use Bot Without Any Interrupt.\n•  Please Click On Main Channel For All 18+ Contents..\n\n•  अब आप बिना किसी रुकावट के बॉट का उपयोग कर सकते हैं।\n•  **•  कृपया सभी 18+ वीडियो के लिए Main Channel पर क्लिक करें |**\n 👇🏻👇🏻👇🏻",
        buttons=keyboard
    )
