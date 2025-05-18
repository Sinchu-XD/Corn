from telethon import events, Button
from Database import save_file  # Your DB logic
from Config import Config
from Bot import bot
from Decorators import owner_or_sudo
import asyncio

MAX_FILE_SIZE_MB = 1024  # 1GB max

# Temporary user sessions for flow tracking
user_states = {}

@bot.on(events.NewMessage(func=owner_or_sudo))
async def handle_file(event):
    if not event.is_private:
        return await event.reply("❌ This command can only be used in private chats.")

    if not event.media:
        return await event.reply("❌ Please send a media file.")

    sender_id = event.sender_id
    file_size = 0
    file_type = ""
    try:
        media = event.media
        if hasattr(media, 'document'):
            file_type = "document"
            file_size = media.document.size
        elif hasattr(media, 'photo'):
            file_type = "photo"
            file_size = await media.photo.get_size()
        elif hasattr(media, 'video'):
            file_type = "video"
            file_size = media.video.size
        elif hasattr(media, 'audio'):
            file_type = "audio"
            file_size = media.audio.size
        else:
            file_type = "unknown"
    except Exception as e:
        return await event.reply("❌ Couldn't process media.")

    file_size_mb = file_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return await event.reply(f"❌ File too large! Max size is {MAX_FILE_SIZE_MB} MB.")

    # Save file
    file_ref_id = await save_file(
        user_id=sender_id,
        chat_id=event.chat_id,
        message_id=event.id,
        file_type=file_type,
    )

    link = f"https://t.me/{Config.BOT_USERNAME}?start={file_ref_id}"
    await event.reply(
        f"✅ File saved!\n\n🔗 **Link:** `{link}`\n🆔 **Ref ID:** `{file_ref_id}`\n"
        f"📦 **Type:** {file_type}\n💾 **Size:** {file_size_mb:.2f} MB\n\n"
        f"📸 Now send 1 or more **thumbnail images**.\nSend `/done` when finished or `/cancel` to abort.",
        parse_mode="md"
    )

    # Initialize user state
    user_states[sender_id] = {
        "file_link": link,
        "ref_id": file_ref_id,
        "thumbs": [],
        "step": "thumbnail"
    }

    # Wait for thumbnail step
    try:
        while True:
            thumb_event = await bot.wait_for(events.NewMessage(from_users=sender_id), timeout=120)

            if thumb_event.raw_text.lower() == "/cancel":
                user_states.pop(sender_id, None)
                return await thumb_event.reply("❌ Upload cancelled.")

            if thumb_event.raw_text.lower() == "/done":
                if not user_states[sender_id]["thumbs"]:
                    await thumb_event.reply("❗ Send at least one thumbnail or `/cancel`.")
                    continue
                break

            if not thumb_event.photo:
                await thumb_event.reply("❗ Please send a valid image or `/done` to finish.")
                continue

            user_states[sender_id]["thumbs"].append(thumb_event.photo)
            await thumb_event.reply("✅ Thumbnail saved. Send more or `/done` to finish.")

        # Ask for title
        await event.respond("📝 Now send the **title** for your post:")

        title_event = await bot.wait_for(events.NewMessage(from_users=sender_id), timeout=120)
        if title_event.raw_text.lower() == "/cancel":
            user_states.pop(sender_id, None)
            return await title_event.reply("❌ Upload cancelled.")

        user_states[sender_id]["title"] = title_event.text

        # Ask for channel
        await event.respond("📢 Finally, send the **channel ID** to post this (e.g. `@channel` or `-100...`).")

        channel_event = await bot.wait_for(events.NewMessage(from_users=sender_id), timeout=120)
        if channel_event.raw_text.lower() == "/cancel":
            user_states.pop(sender_id, None)
            return await channel_event.reply("❌ Upload cancelled.")

        channel_id = channel_event.raw_text.strip()
        title = user_states[sender_id]["title"]
        thumbs = user_states[sender_id]["thumbs"]
        link = user_states[sender_id]["file_link"]

        # Prepare button and caption
        buttons = [Button.url("📺 Watch", url=link)]

        if len(thumbs) == 1:
            await bot.send_file(
                channel_id,
                thumbs[0],
                caption=f"**{title}**",
                buttons=buttons,
                parse_mode="md"
            )
        else:
            media_group = []
            for i, thumb in enumerate(thumbs):
                caption = f"**{title}**" if i == 0 else None
                media_group.append(
                    bot._build_media_message(
                        file=thumb,
                        caption=caption,
                        parse_mode="md"
                    )
                )
            # Send first image separately with button
            await bot.send_file(
                channel_id,
                thumbs[0],
                caption=f"**{title}**",
                buttons=buttons,
                parse_mode="md"
            )
            for thumb in thumbs[1:]:
                await bot.send_file(channel_id, thumb)

        # Send same to log channel
        await bot.send_file(
            Config.LOG_CHANNEL_ID,
            thumbs[0],
            caption=f"**{title}**\n\n🔗 [Watch]({link})",
            parse_mode="md",
            buttons=buttons
        )

        await channel_event.reply("✅ Posted successfully!")

    except asyncio.TimeoutError:
        user_states.pop(sender_id, None)
        return await event.reply("⌛ Timeout. Please start again.")
