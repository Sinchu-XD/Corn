from telethon import events
from telethon.errors import (
    UserAlreadyParticipantError,
    InviteHashInvalidError,
    InviteHashExpiredError,
    ChannelPrivateError
)
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
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


@bot.on(events.NewMessage(pattern=r"/addchannel(?:\s+(.+))?"))
async def add_channel_cmd(event: events.NewMessage.Event):
    if not await owner_or_sudo(event):
        return

    args = event.pattern_match.group(1)
    if not args:
        return await event.reply("Usage: `/addchannel @username` or invite link")

    raw = extract_channel_input(args)

    try:
        # Try public @username channel
        entity = await bot.get_entity(raw)
        ch_id = entity.username or f"private:{entity.id}"
        await add_channel(ch_id)
        return await event.reply(f"✅ Added `{entity.title}` to required join list.")
    except (ChannelPrivateError, ValueError):
        pass

    if raw.startswith("+"):  # Private invite link
        try:
            chat = await bot(ImportChatInviteRequest(hash=raw))
            entity = chat.chats[0]
            await add_channel(f"private:{entity.id}")
            return await event.reply(f"✅ Added private channel `{entity.title}` to required join list.")
        except InviteHashInvalidError:
            return await event.reply("❌ Invalid invite link.")
        except InviteHashExpiredError:
            return await event.reply("❌ Invite link has expired.")
        except UserAlreadyParticipantError:
            try:
                chat = await bot(CheckChatInviteRequest(raw))
                entity = chat.chat
                await add_channel(f"private:{entity.id}")
                return await event.reply(f"✅ Added private channel `{entity.title}` to required join list.")
            except Exception:
                return await event.reply("❌ Failed to resolve invite link.")
        except Exception:
            return await event.reply("❌ Failed to resolve channel. Make sure the bot is added and link is correct.")
    else:
        return await event.reply("❌ Invalid input. Use @username or a valid invite link.")


@bot.on(events.NewMessage(pattern=r"/rmchannel(?:\s+(.+))?"))
async def remove_channel_cmd(event: events.NewMessage.Event):
    if not await owner_or_sudo(event):
        return

    args = event.pattern_match.group(1)
    if not args:
        return await event.reply("Usage: `/rmchannel @username` or channel ID")

    ch = extract_channel_input(args)
    if ch.startswith("+"):
        return await event.reply("Use the stored private ID to remove private channels manually.")
    await remove_channel(ch)
    await event.reply(f"❌ Removed `{ch}` from required join list.")


@bot.on(events.NewMessage(pattern="/channelslist"))
async def list_channels_cmd(event: events.NewMessage.Event):
    if not await owner_or_sudo(event):
        return

    channels = await get_channels()
    if not channels:
        return await event.reply("No required channels set.")
    msg = "**📢 Required Channels:**\n" + "\n".join([f"- `{ch}`" for ch in channels])
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
