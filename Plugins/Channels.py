from pyrogram import Client, filters
from pyrogram.types import Message
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
    if raw.startswith("https://t.me/"):
        raw = raw.replace("https://t.me/", "")
    elif raw.startswith("t.me/"):
        raw = raw.replace("t.me/", "")
    if raw.startswith("@"):
        raw = raw[1:]
    return raw

@bot.on_message(filters.command("addchannel") & owner_or_sudo)
async def add_channel_cmd(c: Client, m: Message):
    if len(m.command) < 2:
        return await m.reply("Usage: `/addchannel @channelusername`")
    ch = extract_channel_input(m.command[1])
    await add_channel(ch)
    await m.reply(f"✅ Added `{ch}` to required join list.")

@bot.on_message(filters.command("rmchannel") & owner_or_sudo)
async def remove_channel_cmd(c: Client, m: Message):
    if len(m.command) < 2:
        return await m.reply("Usage: `/rmchannel @channelusername`")
    ch = extract_channel_input(m.command[1])
    await remove_channel(ch)
    await m.reply(f"❌ Removed `{ch}` from required join list.")

@bot.on_message(filters.command("channelslist") & owner_or_sudo)
async def list_channels_cmd(c: Client, m: Message):
    channels = await get_channels()
    if not channels:
        return await m.reply("No required channels set.")
    msg = "**📢 Required Channels:**\n" + "\n".join([f"- `{ch}`" for ch in channels])
    await m.reply(msg)

@bot.on_message(filters.command("mainchannel") & owner_or_sudo)
async def set_or_get_main_channel(c: Client, m: Message):
    if len(m.command) == 1:
        main_ch = await get_main_channel()
        if not main_ch:
            return await m.reply("🚫 Main channel not set.")
        return await m.reply(f"📢 **Main Channel:** `{main_ch}`")
    
    ch = extract_channel_input(m.command[1])
    await set_main_channel(ch)
    await m.reply(f"✅ Set `{ch}` as the **Main Channel**.")
