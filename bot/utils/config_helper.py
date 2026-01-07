"""
Config helper utilities for getting forward configurations.
"""
from typing import Any, Dict, Optional

from pyrogram.types import Message

from bot.config import settings
from bot.utils.helpers import get_link_parts

__all__ = ["get_config_from_dest_link"]


async def get_config_from_dest_link(message: Message, link: str) -> Optional[Dict[str, Any]]:
    """
    Get config for the source channel from a link. If source has only one destination,
    return it directly. Otherwise, ask user for destination link.
    
    Args:
        message: The message object to use for asking
        link: The source message link to parse
        
    Returns:
        Matching config dict or None if not found/error
    """
    # Parse the source link to get chat ID
    parts = get_link_parts(link)
    if not parts:
        await message.reply_text("❌ Invalid source link")
        return None
    
    source_chat_id = parts[0]
    
    # Find all configs for this source
    source_configs = [
        config for config in settings.FORWARD_CONFIG 
        if config.get("source") == source_chat_id
    ]
    
    # If no configs found for this source
    if not source_configs:
        await message.reply_text("❌ No config found for this source")
        return None
    # If only one config for this source, return it directly
    elif len(source_configs) == 1:
        return source_configs[0]
    # If multiple configs for this source, ask which destination
    else:
        text = f"📍 Found {len(source_configs)} destinations for this source.\n\n"
        text += "Available destinations:\n"
        for i, config in enumerate(source_configs, 1):
            dest_id = config.get("dest")
            text += f"{i}. `{dest_id}`\n"
        text += "\nPlease send the destination ID (copy-paste from above):\n\n"
        text += "/cancel to cancel ❌"
        
        ask = await message.chat.ask(text)
        
        if not ask or not ask.text:
            return None
            
        if ask.text.lower() in ["/cancel", "cancel"]:
            return None
        
        # Try to parse as destination ID directly
        try:
            dest_chat_id = int(ask.text.strip())
        except ValueError:
            await message.reply_text("❌ Invalid destination ID. Please send a valid number.")
            return None
        
        # Find matching config from source_configs
        for config in source_configs:
            if config.get("dest") == dest_chat_id:
                return config
        
        await message.reply_text(f"❌ No config found for destination: {dest_chat_id}")
        return None
