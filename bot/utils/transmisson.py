import os
import time
import uuid
from contextlib import suppress

from pyrogram import Client, types

from bot.config import settings
from bot.enums import TransferStatus
from bot.exceptions import CancelledError
from bot.utils.ffmpeg import get_video_details
from bot.utils.helpers import (
    get_thumbnail,
    get_title,
    get_upload_function,
    is_transfer_cancelled,
    preserve_username,
    progress_for_pyrogram,
    restore_username,
)
from bot.utils.translator import translate
from database import db


async def forward_message(
    bot: Client, app: Client, message: types.Message, user_id: int, config: dict
):
    valid_channels = []
    chat_id = message.chat.id

    user_channels = await db.user_channels.filter_documents({"user_id": user_id})
    for channel in user_channels:
        if not channel["status"]:
            continue

        try:
            await bot.get_chat(channel["channel_id"])
        except Exception as e:
            await bot.floodwait_handler(
                bot.send_message,
                user_id,
                f"Chat not found - {channel['channel_id']} - {e}",
            )
            continue

        valid_channels.append(channel)

    file_path = None

    if message.text:
        unique_key = str(uuid.uuid4())
        orginal_text = message.text.html
        text = preserve_username(config, orginal_text, unique_key)
        text = await translate(text, target_lang=config["lang"])
        text = restore_username(text, unique_key)
        log = await app.send_message(chat_id=config["dest"], text=text)
    else:
        file_path = await download_media(bot, user_id, message)
        if file_path:
            log, file_path = await upload_media(
                user_id, bot, app, file_path,  message, config
            )
        else:
            return

    if not log:
        return await bot.send_message(
            user_id, "Failed to forward the message. Please try again."
        )

    caption = log.text or log.caption or ""

    for channel in valid_channels:
        topic_id = channel["topic_id"]
        paid_star = (
            channel["paid_media"]["stars"] if channel["paid_media"]["status"] else None
        )
        kwargs = {}

        if paid_star and (message.photo or message.video):
            # send using paid media
            if message.photo:
                media = types.InputMediaPhoto(log.photo.file_id)
            elif message.video:
                media = types.InputMediaVideo(log.video.file_id)
            await bot.floodwait_handler(
                bot.send_paid_media,
                chat_id=channel["channel_id"],
                stars_amount=paid_star,
                media=[media],
                caption=caption,
                # reply_markup=message.reply_markup,
                reply_to_message_id=topic_id,
            )
        elif message.media:
            await bot.floodwait_handler(
                log.copy,
                channel["channel_id"],
                message_thread_id=topic_id,
                caption=caption,
                reply_markup=message.reply_markup,
                **kwargs,
            )
        else:
            await bot.floodwait_handler(
                bot.send_message,
                channel["channel_id"],
                caption,
                reply_markup=message.reply_markup,
                message_thread_id=topic_id,
            )

    if file_path:
        os.remove(file_path)

    if is_transfer_cancelled(message.download_id):
        raise CancelledError


async def download_media(bot, user_id, message: types.Message):
    download_id = message.download_id  # This is the download id of the message

    media = message.document or message.video or message.photo or message.audio
    if not media:
        return None

    out = await bot.floodwait_handler(
        bot.send_message, user_id, f"Downloading ({message.index})"
    )
    start = time.time()

    filename = get_file_name(message)

    if not filename:
        await out.delete()
        await bot.send_message(user_id, "No file name found.")
        return None

    file_path = await bot.floodwait_handler(
        message.download,
        file_name=filename,
        progress=progress_for_pyrogram,
        progress_args=(
            start,
            message,
            out.edit,
            download_id,
            f"Downloading ({message.index})",
        ),
    )
    await out.delete()
    if not file_path:
        raise CancelledError
    return file_path


async def upload_media(
    user_id: int,
    bot: Client,
    app: Client,
    file_path: str,
    message: types.Message,
    config: dict,
):
    bot.send_paid_media
    out = await bot.floodwait_handler(bot.send_message, user_id, "Starting upload...")
    target_channel = config["dest"]
    upload_instance = bot
    function = None

    thumbnail = await get_thumbnail(file_path)

    function, kwargs = await get_upload_function(message, upload_instance, file_path)

    if not function:
        await out.delete()
        return await bot.send_message(
            user_id, "Invalid file upload mode. Please select a valid file upload mode."
        )

    if function == upload_instance.send_video:
        width, height, duration = await get_video_details(file_path)
        kwargs["duration"] = duration
        kwargs["width"] = width
        kwargs["height"] = height

    kwargs["chat_id"] = target_channel

    media = ["audio", "document", "video", "photo"]
    if any(media_type in kwargs for media_type in media) and thumbnail:
        kwargs["thumb"] = thumbnail

    title = get_title(message)

    if title:
        kwargs["file_name"] = title

    kwargs["progress"] = progress_for_pyrogram
    kwargs["progress_args"] = (
        time.time(),
        message,
        out.edit,
        message.download_id,
        f"Uploading ({message.index})",
    )
    print("upload start")

    caption = message.text or message.caption
    if caption:
        unique_key = str(uuid.uuid4())
        caption = caption.html
        caption = preserve_username(config, caption, unique_key)
        caption = await translate(caption, target_lang=config["lang"])
        caption = restore_username(caption, unique_key)

    kwargs["caption"] = caption

    await bot.floodwait_handler(out.edit, "Uploading...")

    log = await bot.floodwait_handler(function, **kwargs)
    await out.delete()
    if thumbnail:
        os.remove(thumbnail)
    if not log:
        raise CancelledError

    if caption:
        with suppress(Exception):
            await app.edit_message_caption(
                chat_id=target_channel,
                message_id=log.id,
                caption=caption,
            )

    log = await bot.get_messages(log.chat.id, log.id)
    return log, file_path


async def resume_transfers(bot: Client):
    transfers = await db.transfers.filter_documents(
        {
            "status": {
                "$in": [TransferStatus.SLEEPING.value, TransferStatus.IN_PROGRESS.value]
            }
        }
    )
    for transfer in transfers:
        user_id = transfer["user_id"]
        text = f"**Bot has been restarted. You can resume your transfers now from {transfer['link_index']} to {len(transfer['links'])}.**"
        markup = types.InlineKeyboardMarkup(
            [
                [
                    types.InlineKeyboardButton(
                        "Resume Transfers",
                        callback_data=f"resume_transfers {transfer['_id']}",
                    )
                ]
            ]
        )
        try:
            await bot.send_message(user_id, text, reply_markup=markup)
        except Exception as e:
            print(e)

        await update_transfer(transfer["_id"], status=None)


async def add_transfer_to_queue(
    user_id, download_id, links, link_index, status, **kwargs
):
    settings.TRANSFERS[download_id] = {
        "user_id": user_id,
        "links": links,
        "link_index": link_index,
        "status": status,
    }

    return await db.transfers.create(
        user_id, download_id, links, link_index, status, **kwargs
    )


async def remove_transfer_from_queue(download_id):
    settings.TRANSFERS.pop(download_id, None)
    return await db.transfers.delete(download_id)


async def update_transfer(download_id, **kwargs):
    if download_id in settings.TRANSFERS:
        settings.TRANSFERS[download_id].update(kwargs)
    return await db.transfers.update(download_id, kwargs)


def get_file_name(message: types.Message):
    if not message.media:
        return None

    media = getattr(message, message.media.value, None)
    if not media:
        return None

    file_name = getattr(media, "file_name", None)

    if file_name:
        return file_name

    # Mapping of media types to their extensions
    media_extensions = {"photo": ".jpg", "video": ".mp4", "audio": ".mp3"}

    # Get the media type and extension
    media_type = message.media.value
    if media_type in media_extensions:
        return f"{media.file_id}{media_extensions[media_type]}"

    return None


def get_extension(file_name):
    return file_name.split(".")[-1]
