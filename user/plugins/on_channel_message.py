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

from pyrogram import Client, filters
from pyrogram.types import Message
from bot.config import Config, ContextVariables
from bot.plugins.on_https_message import on_https_message
import logging

logger = logging.getLogger(__name__)


@Client.on_message(

)
async def on_channel_message(bot: Client, message: Message):
    """
    Automatically process messages from ON_MESSAGE_SOURCE channel
    """

    if message.chat.id != Config.ON_MESSAGE_SOURCE:
        return

    logger.info(f"New message received from source channel: {message.text.html}")
    
    # Build the message link
    if message.chat.username:
        # Public channel
        link = f"https://t.me/{message.chat.username}/{message.id}"
    else:
        # Private channel
        chat_id = str(message.chat.id).replace("-100", "")
        link = f"https://t.me/c/{chat_id}/{message.id}"
    
    logger.info(f"Extracted link: {link}")
    
    # Create a fake user message to pass to the handler
    # We'll use the OWNER_ID as the user who requested this
    user_message = message
    user_message.text = link
    user_message.from_user = type('obj', (object,), {'id': Config.OWNER_ID})()
    user_message._client = ContextVariables.BOT
    user_message.chat = type('obj', (object,), {'id': Config.OWNER_ID})()
    
    # Call the HTTPS handler to process the link
    await on_https_message(ContextVariables.BOT, user_message, is_batch=False)
