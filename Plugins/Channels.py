from telethon import events
from telethon.tl.types import Message
from telethon.errors import (
    UserAlreadyParticipantError,
    InviteHashInvalidError,
)
from telethon.tl.functions.messages import ImportChatInviteRequest

from Bot import bot
from Database import (
    add_channel,
    remove_channel,
    get_channels,
    set_main_channel,
    get_main_channel
)
from Decorators import owner_or_sudo


# ✅ Resolves both public usernames and private invite links
async def resolve_channel_input(raw: str):
    raw = raw.strip()

    if raw.startswith("https://t.me/"):
        raw = raw.replace("https://t.me/", "")
    elif raw.startswith("t.me/"):
        raw = raw.replace("t.me/", "")

    if raw.startswith("+"):  # Private channel invite link
        try:
            result = await bot(ImportChatInviteRequest(raw))
            chat = result.chats[0]
            return f"private:{chat.id}"
        except UserAlreadyParticipantError:
            return f"private:{chat.id}"
        except InviteHashInvalidError:
            return None
        except Exception as e:
            print(f"[Invite Resolve Error] {e}")
            return None
    else:
        return raw.lstrip("@")


@bot.on(events.NewMessage(pattern=r"/addchannel(?:\s+(.+))?"))
async def add_channel_cmd(event: events.NewMessage.Event):
    if not await owner_or_sudo(event):
        return

    args = event.pattern_match.group(1)
    if not args:
        return await event.reply("Usage: `/addchannel @channelusername or https://t.me/+invitecode`")

    ch = await resolve_channel_input(args)
    if not ch:
        return await event.reply("❌ Failed to resolve channel. Make sure the bot is added and link is correct.")

    await add_channel(ch)
    await event.reply(f"✅ Added `{ch}` to required join list.")


@bot.on(events.NewMessage(pattern=r"/rmchannel(?:\s+(.+))?"))
async def remove_channel_cmd(event: events.NewMessage.Event):
    if not await owner_or_sudo(event):
        return

    args = event.pattern_match.group(1)
    if not args:
        return await event.reply("Usage: `/rmchannel @channelusername or https://t.me/+invitecode`")

    ch = await resolve_channel_input(args)
    if not ch:
        return await event.reply("❌ Failed to resolve channel. Make sure the link is correct.")

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

    ch = await resolve_channel_input(arg)
    if not ch:
        return await event.reply("❌ Failed to resolve channel. Make sure the link is correct.")

    await set_main_channel(ch)
    await event.reply(f"✅ Set `{ch}` as the **Main Channel**.")
