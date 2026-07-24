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

from pyrogram import Client, filters
from pyrogram.types import Message

from bot.config import ContextVariables, settings
from bot.plugins.on_https_message import on_https_message
from database import db

logger = logging.getLogger(__name__)


def _build_message_link(message: Message) -> str:
    chat = message.chat
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{message.id}"
    chat_id = str(chat.id).replace("-100", "")
    return f"https://t.me/c/{chat_id}/{message.id}"


@Client.on_message(filters.chat(settings.ON_MESSAGE_SOURCE))
async def on_channel_message(bot: Client, message: Message):
    """
    Automatically process messages from ON_MESSAGE_SOURCE channel
    """

    original_chat = message.chat
    link = _build_message_link(message)
    text = message.text or message.caption or ""

    # Keep last 1000 source msgs (deduped by source + message id)
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
