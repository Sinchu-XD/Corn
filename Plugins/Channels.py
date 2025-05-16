from telethon import events
from telethon.errors import (
    InviteHashInvalidError,
    InviteHashExpiredError,
    UserAlreadyParticipantError,
)
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from Bot import bot
from Database import (
    add_channel,
    remove_channel,
    get_channels,
    set_main_channel,
    get_main_channel,
)
from Decorators import owner_or_sudo


def extract_channel_input(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("https://t.me/"):
        raw = raw.replace("https://t.me/", "")
    elif raw.startswith("t.me/"):
        raw = raw.replace("t.me/", "")
    if raw.startswith("@"):
        raw = raw[1:]
    return raw


@bot.on(events.NewMessage(pattern=r"/addchannel(?:\s+(.+))?"))
async def add_channel_cmd(event: events.NewMessage.Event):
    if not await owner_or_sudo(event):
        return

    args = event.pattern_match.group(1)
    if not args:
        return await event.reply("Usage: `/addchannel @channelusername or invite link`")

    raw = extract_channel_input(args)

    try:
        if raw.startswith("+"):
            try:
                imported = await bot(ImportChatInviteRequest(hash=raw[1:]))
                entity = imported.chats[0]
            except UserAlreadyParticipantError:
                check = await bot(CheckChatInviteRequest(hash=raw[1:]))
                entity = check.chat
        else:
            entity = await bot.get_entity(raw)

        ch_id = entity.username or f"private:{entity.id}"
        await add_channel(ch_id)
        return await event.reply(f"✅ Added `{entity.title}` to required join list.")

    except (InviteHashInvalidError, InviteHashExpiredError):
        return await event.reply("❌ Invalid or expired invite link.")
    except Exception as e:
        return await event.reply(f"❌ Failed to resolve channel.\n**Error:** `{str(e)}`")


@bot.on(events.NewMessage(pattern=r"/rmchannel(?:\s+(.+))?"))
async def remove_channel_cmd(event: events.NewMessage.Event):
    if not await owner_or_sudo(event):
        return

    args = event.pattern_match.group(1)
    if not args:
        return await event.reply("Usage: `/rmchannel @channelusername or invite link`")

    raw = extract_channel_input(args)

    ch_id = raw if not raw.startswith("+") else f"private:{raw[1:]}"
    await remove_channel(ch_id)
    await event.reply(f"❌ Removed `{ch_id}` from required join list.")


@bot.on(events.NewMessage(pattern="/channelslist"))
async def list_channels_cmd(event: events.NewMessage.Event):
    if not await owner_or_sudo(event):
        return

    channels = await get_channels()
    if not channels:
        return await event.reply("No required channels set.")

    msg = "**📢 Required Channels:**\n"
    for ch in channels:
        msg += f"- `{ch}`\n"
    await event.reply(msg)


@bot.on(events.NewMessage(pattern=r"/mainchannel(?:\s+(.+))?"))
async def set_or_get_main_channel(event: events.NewMessage.Event):
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
