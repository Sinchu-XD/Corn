from telethon import events
from Bot import bot
from Database import (
    add_channel,
    remove_channel,
    get_channels,
    set_main_channel,
    get_main_channel
)
from Decorators import owner_or_sudo


def extract_channel_input(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("https://t.me/"):
        raw = raw.replace("https://t.me/", "")
    elif raw.startswith("t.me/"):
        raw = raw.replace("t.me/", "")
    return raw  # Keep +invite links intact


@bot.on(events.NewMessage(pattern=r"/addchannel(?:\s+(.+))?"))
async def add_channel_cmd(event):
    if not await owner_or_sudo(event):
        return

    args = event.pattern_match.group(1)
    if not args:
        return await event.reply("Usage: `/addchannel <channel_link or @username>`")

    ch = extract_channel_input(args)
    await add_channel(ch)
    await event.reply(f"✅ Added `{ch}` to required channel list.")


@bot.on(events.NewMessage(pattern=r"/rmchannel(?:\s+(.+))?"))
async def remove_channel_cmd(event):
    if not await owner_or_sudo(event):
        return

    args = event.pattern_match.group(1)
    if not args:
        return await event.reply("Usage: `/rmchannel <channel_link or @username>`")

    ch = extract_channel_input(args)
    await remove_channel(ch)
    await event.reply(f"❌ Removed `{ch}` from required channel list.")


@bot.on(events.NewMessage(pattern="/channelslist"))
async def list_channels_cmd(event):
    if not await owner_or_sudo(event):
        return

    channels = await get_channels()
    if not channels:
        return await event.reply("📭 No channels saved.")

    msg = "**📢 Required Channels:**\n" + "\n".join([f"- `{ch}`" for ch in channels])
    await event.reply(msg)


@bot.on(events.NewMessage(pattern=r"/mainchannel(?:\s+(.+))?"))
async def set_or_get_main_channel(event):
    if not await owner_or_sudo(event):
        return

    arg = event.pattern_match.group(1)
    if not arg:
        main_ch = await get_main_channel()
        if not main_ch:
            return await event.reply("🚫 Main channel not set.")
        return await event.reply(f"📢 **Main Channel:** `{main_ch}`")

    ch = extract_channel_input(arg)
    await set_main_channel(ch)
    await event.reply(f"✅ Set `{ch}` as the **Main Channel**.")
