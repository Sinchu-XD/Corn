from telethon import events
from Database import save_file  # Your DB logic to store chat_id + message_id
from Config import Config
from Bot import bot
from Decorators import owner_or_sudo
import os
from datetime import datetime

MAX_FILE_SIZE_MB = 1024  # Maximum allowed file size in MB (1GB)

@bot.on(events.NewMessage(func=owner_or_sudo))
async def handle_file(event):
    # ✅ Only allow in private chat
    if not event.is_private:
        return await event.reply("❌ This command can only be used in private chats.")

    # ✅ Check for media (Telethon doesn't use .photo/.video like Bot API)
    if not event.media:
        return await event.reply("❌ Please send a photo, video, or document.")

    # ✅ Get file size and check if it exceeds the maximum allowed size
    file_size = 0
    file_type = ""
    media_type = event.media
    try:
        if hasattr(media_type, 'document'):
            file_type = "document"
            file_size = media_type.document.size
        elif hasattr(media_type, 'photo'):
            file_type = "photo"
            file_size = await media_type.photo.get_size()
        elif hasattr(media_type, 'video'):
            file_type = "video"
            file_size = media_type.video.size
        elif hasattr(media_type, 'audio'):
            file_type = "audio"
            file_size = media_type.audio.size
        else:
            file_type = "unknown"
    except Exception as e:
        print(f"[ERROR] Failed to get file size: {e}")
    
    # Check file size
    file_size_mb = file_size / (1024 * 1024)  # Convert bytes to MB
    if file_size_mb > MAX_FILE_SIZE_MB:
        return await event.reply(f"❌ The file is too large! Maximum allowed size is {MAX_FILE_SIZE_MB} MB.")
    # ✅ Save file metadata using chat_id + message_id (not file_id)
    file_info = {
        "chat_id": event.chat_id,
        "message_id": event.id,
        "file_type": file_type,
        "file_size": file_size_mb,
        "uploaded_by": event.sender_id,
    }

    # ✅ save_file should return a unique reference ID (Mongo ID or UUID)
    file_ref_id = await save_file(
        user_id=event.sender_id,
        chat_id=event.chat_id,
        message_id=event.id,
        file_type=file_type,
    )

    # ✅ Link format
    link = f"https://t.me/{Config.BOT_USERNAME}?start={file_ref_id}"
    # ✅ Confirm to user
    await event.reply(
        f"✅ File saved!\n\n🔗 **Here's your link:**\n`{link}`\n🆔 **File Ref ID:** `{file_ref_id}`\n"
        f"📦 **File Type:** {file_type}\n💾 **File Size:** {file_size_mb:.2f} MB",
        parse_mode="md"
    )

    # ✅ Log upload
    try:
        # Get user mention manually
        sender = await event.get_sender()
        mention = f"[{sender.first_name}](tg://user?id={sender.id})"
        await bot.send_message(
            Config.LOG_CHANNEL_ID,
            f"#UPLOAD\n👤 **Uploader:** {mention}\n"
            f"📦 **Type:** {file_type}\n🆔 **File Ref ID:** `{file_ref_id}`\n"
            f"💾 **File Size:** {file_size_mb:.2f} MB\n"
            f"🔗 [Open File Link]({link})",
            parse_mode="md"
        )
    except Exception as e:
        print(f"[LOG ERROR] Failed to log upload: {e}")
        
