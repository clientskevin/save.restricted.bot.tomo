#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: on_channel_message.py
Author: Maria Kevin
Created: 2025-11-17
Description: Automatically saves messages from specified source channel
"""

__author__ = "Maria Kevin"
__version__ = "0.1.0"

import copy
import logging
from contextlib import suppress

from pyrogram import Client, filters
from pyrogram.types import Message

from bot.config import ContextVariables, settings
from bot.plugins.on_https_message import on_https_message
from bot.utils.helpers import get_user_client
from database import db

logger = logging.getLogger(__name__)


def _build_message_link(message: Message) -> str:
    chat = message.chat
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{message.id}"
    chat_id = str(chat.id).replace("-100", "")
    return f"https://t.me/c/{chat_id}/{message.id}"


async def _delete_dest_message(bot: Client, dest_id: int, dest_message_id: int):
    """Delete a dest copy using bot first, then owner user client."""
    with suppress(Exception):
        await bot.delete_messages(dest_id, dest_message_id)
        return True

    app = await get_user_client(settings.OWNER_ID)
    if app:
        with suppress(Exception):
            await app.delete_messages(dest_id, dest_message_id)
            return True

    return False


@Client.on_message(filters.chat(settings.ON_MESSAGE_SOURCE))
async def on_channel_message(bot: Client, message: Message):
    """
    Automatically process messages from ON_MESSAGE_SOURCE channel
    """

    original_chat = message.chat
    link = _build_message_link(message)
    text = message.text or message.caption or ""

    # Keep last 10000 source msgs (deduped by source + message id)
    await db.source_messages.save_message(
        source_id=original_chat.id,
        message_id=message.id,
        link=link,
        text=text,
    )

    for config in settings.FORWARD_CONFIG:
        print(config)
        if config["source"] != original_chat.id:
            print("Skipping", config["source"], original_chat.id)
            continue

        user_message = copy.deepcopy(message)
        user_message.text = link
        user_message.from_user = type("obj", (object,), {"id": settings.OWNER_ID})()
        user_message._client = ContextVariables.BOT
        user_message.chat = type("obj", (object,), {"id": settings.OWNER_ID})()

        await on_https_message(
            ContextVariables.BOT, user_message, is_batch=False, config=config
        )


@Client.on_deleted_messages(filters.chat(settings.ON_MESSAGE_SOURCE))
async def on_channel_message_deleted(bot: Client, messages: list):
    """
    When a source message is deleted, delete matching copies in dest channels.
    """
    if not messages:
        return

    # Deleted updates only carry chat + ids; group by source chat
    by_chat: dict[int, list[int]] = {}
    for msg in messages:
        chat = getattr(msg, "chat", None)
        if not chat:
            continue
        by_chat.setdefault(chat.id, []).append(msg.id)

    bot_client = ContextVariables.BOT or bot

    for source_id, message_ids in by_chat.items():
        records = await db.source_messages.get_messages(source_id, message_ids)
        for record in records:
            forwards = record.get("forwards") or []
            for fwd in forwards:
                dest_id = fwd.get("dest_id")
                dest_message_id = fwd.get("dest_message_id")
                if dest_id is None or dest_message_id is None:
                    continue
                ok = await _delete_dest_message(bot_client, dest_id, dest_message_id)
                if ok:
                    logger.info(
                        "Deleted dest %s/%s for source %s/%s",
                        dest_id,
                        dest_message_id,
                        source_id,
                        record["message_id"],
                    )
                else:
                    logger.warning(
                        "Failed to delete dest %s/%s for source %s/%s",
                        dest_id,
                        dest_message_id,
                        source_id,
                        record["message_id"],
                    )

            await db.source_messages.remove_message(source_id, record["message_id"])
