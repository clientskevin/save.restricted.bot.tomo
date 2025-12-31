#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: delete_all.py
Author: Maria Kevin
Description: 
"""

import asyncio

from pyrogram import Client
from pyrogram.errors import MessageDeleteForbidden, MessageIdInvalid

BOT_TOKEN = "8510885908:AAHY1J-Bc_sbwDB8eX-XYYWKsL25Djg3Onk"
start_message_id = 1448
api_id = 26033244
api_hash = "b06a711dfb9dcb0fbf707758b5117216"
channel_id = -1003490790931
session = "BQGNPFwAsULpstS5pkHdUJPYKUSLfWLfz_4EA1DC1-BpuWfIRzsKYyKGDQgjZsohxogTzFDHe7b98LIAmrKfdWIPgI-dOp--tnjXuj_Un6ZHeBQEbqW4cxIpgjN6gdYMDLlYHDFkl9fK5fVh9zcNxzm_sF0A-j_wnXYcvbiOWfuQbFBseagJ88YIBOlhUi-P-XYTe_uu44z2qQt0scfkJoL99RNfKD6CVJ8mwzTJeYUgsDJMBuFMjOt_AqKOsIOHtpolYrFE6DgsltaqYWFgrqoocTl9PdD1B_8icKTY_yycX83Zw4a7Xe01yOW2mWcbhG2-U0zPvIXeaePQ2QXirJfDdfeXtAAAAAAeAPHfAA"
last_message_id = 1489

async def delete_messages_to_last():
    app = Client(
        "my_bot_session",
        api_id=api_id,
        api_hash=api_hash,
        # bot_token=BOT_TOKEN,
        session_string=session
    )

    async with app:
        try:
            # Get the last message ID in the channel
            messages_to_delete = list(range(start_message_id, last_message_id + 1))
            
            # Pyrogram's delete_messages can take a list of message IDs
            # It's more efficient to delete in batches if the list is very long,
            # but for a simple range, passing the whole list is fine.
            # However, to handle errors for individual messages, iterating is better.
            
            deleted_count = 0
            for msg_id in messages_to_delete:
                try:
                    r = await app.delete_messages(chat_id=channel_id, message_ids=msg_id)
                    deleted_count += 1
                    print(f"Deleted message {msg_id}: {r}")
                except MessageDeleteForbidden:
                    print(f"Permission denied to delete message {msg_id}. Skipping.")
                except MessageIdInvalid:
                    print(f"Message {msg_id} not found or already deleted. Skipping.")
                except Exception as e:
                    print(f"An unexpected error occurred while deleting message {msg_id}: {e}")
            
            print(f"Successfully attempted to delete {len(messages_to_delete)} messages. {deleted_count} messages were deleted.")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(delete_messages_to_last())

