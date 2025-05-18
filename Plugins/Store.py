from telethon import events, Button
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio
from Database import save_file  # Your DB logic
from Config import Config
from Bot import bot
from Decorators import owner_or_sudo
import asyncio

MAX_FILE_SIZE_MB = 1024  # 1GB max
user_states = {}

@bot.on(events.NewMessage(func=owner_or_sudo))
async def handle_file(event):
    if not event.is_private:
        return await event.reply("❌ This command can only be used in private chats.")

    # If user is already in a flow, ignore new media
    if event.sender_id in user_states:
        return

    if not event.media:
        return await event.reply("❌ Please send a media file.")

    sender_id = event.sender_id
    media = event.media
    file_type = "unknown"
    file_size = 0

    # Determine file type & size
    if getattr(media, "document", None):
        doc = media.document
        file_size = doc.size or 0
        if any(isinstance(a, DocumentAttributeVideo) for a in doc.attributes):
            file_type = "video"
        elif any(isinstance(a, DocumentAttributeAudio) for a in doc.attributes):
            file_type = "audio"
        else:
            file_type = "document"
    elif getattr(media, "photo", None):
        file_type = "photo"
    else:
        return await event.reply("❌ Unsupported media type.")

    # Size check (skip photos if size unknown)
    if file_size and (file_size / (1024*1024)) > MAX_FILE_SIZE_MB:
        return await event.reply(f"❌ File too large! Max is {MAX_FILE_SIZE_MB} MB.")

    # Save and reply with link
    file_ref_id = await save_file(
        user_id=sender_id,
        chat_id=event.chat_id,
        message_id=event.id,
        file_type=file_type,
    )
    link = f"https://t.me/{Config.BOT_USERNAME}?start={file_ref_id}"
    await event.reply(
        f"✅ File saved!\n\n🔗 **Link:** `{link}`\n🆔 **Ref ID:** `{file_ref_id}`\n"
        "📸 Now send thumbnail images (one or more).\n"
        "Send `/done` when finished or `/cancel` to abort.",
        parse_mode="md"
    )

    # Initialize state
    user_states[sender_id] = {
        "file_link": link,
        "ref_id": file_ref_id,
        "thumbs": [],
    }

    try:
        # Start a conversation to gather thumbnails
        async with bot.conversation(event.chat_id, timeout=120) as conv:
            await conv.send_message("📸 Now send thumbnail images (one or more).\nSend `/done` when finished or `/cancel` to abort.")

            while True:
                thumb_msg = await conv.get_response()
                text = thumb_msg.text or ""

                if text.lower() == "/cancel":
                    user_states.pop(sender_id, None)
                    return await thumb_msg.reply("❌ Upload cancelled.")

                if text.lower() == "/done":
                    if not user_states[sender_id]["thumbs"]:
                        await conv.send_message("❗ Send at least one thumbnail or `/cancel`.")
                        continue
                    break

                if not thumb_msg.photo:
                    await conv.send_message("❗ Please send a valid image or `/done` to finish.")
                    continue

                user_states[sender_id]["thumbs"].append(thumb_msg.photo)
                await conv.send_message("✅ Thumbnail saved. Send more or `/done` to finish.")

            # Ask for title
            await conv.send_message("📝 Now send the **title** for your post:")
            title_msg = await conv.get_response()
            if (title_msg.text or "").lower() == "/cancel":
                user_states.pop(sender_id, None)
                return await title_msg.reply("❌ Upload cancelled.")
            title = title_msg.text

            # Ask for channel
            await conv.send_message(
                "📢 Finally, send the **channel ID** (e.g., `@channel` or `-1001234567890`)."
            )
            channel_msg = await conv.get_response()
            if (channel_msg.text or "").lower() == "/cancel":
                user_states.pop(sender_id, None)
                return await channel_msg.reply("❌ Upload cancelled.")
            channel_id = channel_msg.text.strip()

        # Outside conversation: send to target channel
        thumbs = user_states[sender_id]["thumbs"]
        buttons = [Button.url("Click Here To Watch", url=link)]

        # Send first thumb with button & caption
        await bot.send_file(
            channel_id,
            thumbs[0],
            caption=f"**{title}**",
            buttons=buttons,
            parse_mode="md"
        )
        # Send remaining thumbnails without caption/buttons
        for thumb in thumbs[1:]:
            await bot.send_file(channel_id, thumb)

        # Log to LOG_CHANNEL_ID
        await bot.send_file(
            Config.LOG_CHANNEL_ID,
            thumbs[0],
            caption=f"**{title}**\n\n🔗 [Watch]({link})",
            buttons=buttons,
            parse_mode="md"
        )

        await channel_msg.reply("✅ Posted successfully!")

    except asyncio.TimeoutError:
        user_states.pop(sender_id, None)
        return await event.reply("⌛ Timeout. Please start again.")
        
