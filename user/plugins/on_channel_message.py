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

import logging

from pyrogram import Client
from pyrogram.types import Message

from bot.config import ContextVariables, settings
from bot.plugins.on_https_message import on_https_message

logger = logging.getLogger(__name__)


@Client.on_message()
async def on_channel_message(bot: Client, message: Message):
    """
    Automatically process messages from ON_MESSAGE_SOURCE channel
    """

    if message.chat.id not in settings.ON_MESSAGE_SOURCE:
        return

    # Build the message link
    if message.chat.username:
        # Public channel
        link = f"https://t.me/{message.chat.username}/{message.id}"
    else:
        # Private channel
        chat_id = str(message.chat.id).replace("-100", "")
        link = f"https://t.me/c/{chat_id}/{message.id}"

    # Create a fake user message to pass to the handler
    # We'll use the OWNER_ID as the user who requested this
    user_message = message
    user_message.text = link
    user_message.from_user = type("obj", (object,), {"id": settings.OWNER_ID})()
    user_message._client = ContextVariables.BOT
    user_message.chat = type("obj", (object,), {"id": settings.OWNER_ID})()

    # Call the HTTPS handler to process the link
    await on_https_message(ContextVariables.BOT, user_message, is_batch=False)
