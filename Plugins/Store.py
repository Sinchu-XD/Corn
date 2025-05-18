from telethon import events, Button
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio
from Database import save_file  # Your DB logic
from Config import Config
from Bot import bot
from Decorators import owner_or_sudo
import asyncio

MAX_FILE_SIZE_MB = 1024  # 1GB
user_states = {}  # Track user upload sessions

@bot.on(events.NewMessage(func=owner_or_sudo))
async def handle_file(event):
    if not event.is_private:
        return await event.reply("❌ This command can only be used in private chats.")
    if not event.media:
        return await event.reply("❌ Please send a media file.")

    sender_id = event.sender_id
    file_type = "unknown"
    file_size = 0

    try:
        media = event.media

        if hasattr(media, 'document'):
            doc = media.document
            file_size = doc.size or 0

            if any(isinstance(attr, DocumentAttributeVideo) for attr in doc.attributes):
                file_type = "video"
            elif any(isinstance(attr, DocumentAttributeAudio) for attr in doc.attributes):
                file_type = "audio"
            else:
                file_type = "document"

        elif hasattr(media, 'photo'):
            file_type = "photo"
            file_size = 0  # Photo sizes are generally small

        else:
            return await event.reply("❌ Unsupported media type.")

    except Exception as e:
        return await event.reply(f"❌ Media processing error: {str(e)}")

    if file_size and (file_size / (1024 * 1024)) > MAX_FILE_SIZE_MB:
        return await event.reply(f"❌ File too large! Max allowed is {MAX_FILE_SIZE_MB} MB.")

    file_ref_id = await save_file(
        user_id=sender_id,
        chat_id=event.chat_id,
        message_id=event.id,
        file_type=file_type
    )

    link = f"https://t.me/{Config.BOT_USERNAME}?start={file_ref_id}"
    await event.reply(
        f"✅ File saved!\n\n🔗 **Link:** `{link}`\n🆔 **Ref ID:** `{file_ref_id}`\n"
        f"📦 **Type:** {file_type}\n\n"
        f"📸 Now send 1 or more **thumbnail images**.\nSend `/done` when finished or `/cancel` to abort.",
        parse_mode="md"
    )

    user_states[sender_id] = {
        "file_link": link,
        "ref_id": file_ref_id,
        "thumbs": [],
        "step": "thumbnail"
    }

    try:
        while True:
            msg = await bot.wait_for(events.NewMessage(from_users=sender_id), timeout=120)

            if msg.raw_text.lower() == "/cancel":
                user_states.pop(sender_id, None)
                return await msg.reply("❌ Upload cancelled.")

            if msg.raw_text.lower() == "/done":
                if not user_states[sender_id]["thumbs"]:
                    await msg.reply("❗ Send at least one thumbnail or `/cancel`.")
                    continue
                break

            if not msg.photo:
                await msg.reply("❗ Please send a valid image or `/done` to finish.")
                continue

            user_states[sender_id]["thumbs"].append(msg.photo)
            await msg.reply("✅ Thumbnail saved. Send more or `/done` to finish.")

        await event.respond("📝 Now send the **title** for your post:")
        title_event = await bot.wait_for(events.NewMessage(from_users=sender_id), timeout=120)
        if title_event.raw_text.lower() == "/cancel":
            user_states.pop(sender_id, None)
            return await title_event.reply("❌ Upload cancelled.")
        title = title_event.text

        await event.respond("📢 Finally, send the **channel ID** (e.g. `@channel` or `-100...`):")
        channel_event = await bot.wait_for(events.NewMessage(from_users=sender_id), timeout=120)
        if channel_event.raw_text.lower() == "/cancel":
            user_states.pop(sender_id, None)
            return await channel_event.reply("❌ Upload cancelled.")
        channel_id = channel_event.raw_text.strip()

        thumbs = user_states[sender_id]["thumbs"]
        buttons = [Button.url("📺 Watch", url=link)]

        try:
            await bot.send_file(
                channel_id,
                thumbs[0],
                caption=f"**{title}**",
                buttons=buttons,
                parse_mode="md"
            )
            for thumb in thumbs[1:]:
                await bot.send_file(channel_id, thumb)

            await bot.send_file(
                Config.LOG_CHANNEL_ID,
                thumbs[0],
                caption=f"**{title}**\n\n🔗 [Watch]({link})",
                buttons=buttons,
                parse_mode="md"
            )
            await channel_event.reply("✅ Posted successfully!")

        except Exception as e:
            return await channel_event.reply(f"❌ Failed to post to channel: `{str(e)}`")

    except asyncio.TimeoutError:
        user_states.pop(sender_id, None)
        return await event.reply("⌛ Timeout. Please start again.")
        
