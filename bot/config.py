from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pyrogram.client import Client
from pyrogram.enums import MessageMediaType

from bot.enums import CaptionVariables


class Config(BaseSettings):
    """
    Application configuration using Pydantic BaseSettings.
    Loads from environment variables and .env files.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "config.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required settings
    API_ID: int
    API_HASH: str
    BOT_TOKEN: str

    # Database settings
    DATABASE_NAME: str = "tg_bot"
    DATABASE_URL: Optional[str] = None
    OWNER_ID: int

    # Optional settings
    WEB_SERVER: bool = False
    WEB_URL: Optional[str] = None
    SLEEP_TIME: int = 10

    # Config file path for forward configuration
    CONFIG_FILE: str = Field(
        default="dev_config.yaml", description="Path to YAML config file"
    )

    # Runtime attributes (not from env)
    CLIENTS: Dict[Any, Any] = Field(default_factory=dict, exclude=True)
    TRANSFERS: Dict[Any, Any] = Field(default_factory=dict, exclude=True)
    FORWARD_CONFIG: Dict[int, Dict[str, Any]] = Field(
        default_factory=dict, exclude=True
    )
    ON_MESSAGE_SOURCE: list = Field(default_factory=list, exclude=True)

    ALL_MEDIA_TYPES: Dict[str, str] = Field(
        default_factory=lambda: {
            MessageMediaType.PHOTO.value: "📷 Photo",
            MessageMediaType.VIDEO.value: "🎥 Video",
            MessageMediaType.AUDIO.value: "🎵 Audio",
            MessageMediaType.DOCUMENT.value: "📄 Document",
            "text": "📄 Text",
        },
        exclude=True,
    )

    @field_validator("WEB_SERVER", mode="before")
    @classmethod
    def parse_bool(cls, v: Any) -> bool:
        """Parse boolean values from string environment variables."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ["true", "yes", "1", "enable", "y"]
        return False

    @model_validator(mode="after")
    def load_forward_config(self) -> "Config":
        """Load forward configuration from YAML file."""
        config_path = Path(self.CONFIG_FILE)
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        self.FORWARD_CONFIG = {int(k): v for k, v in yaml_data["forwards"].items()}
        self.ON_MESSAGE_SOURCE = list(self.FORWARD_CONFIG.keys())
        return self


# Create a singleton instance
settings = Config()


class ContextVariables(object):
    BOT: Client | None = None


class Script(object):
    START_MESSAGE = """💾 **Welcome to the Ultimate Content Saver Bot on Telegram!** 💾

**Steps to Get Started:**
1. **Log in** to your account by sending /account along with your Phone number. 🔑  
2. **Send me any message link**, and I'll safely store it for you! 🗂️  
3. **Explore my advanced features** by tapping the **Settings** button below. ⚙️"""

    RESTART_MESSAGE = "🔄 ** Bot is restarting, please re download your in progress files after few seconds **"

    HELP_MESSAGE_1 = """**💡 Help Section:**

1. **🔐 How to Login:**  
   To login, simply type /account and click on login button, then enter your phone number and verification code.

2. **📥 How to Upload:**  
   After logging in, just copy and paste the message link from any channel or group to upload content.

3. **❓ Need More Help?**  
   Feel free to contact our support team for any queries or assistance.
"""

    DEFAULT_CAPTION = "{%s}" % CaptionVariables.CAPTION.value
    PROGRESS_MESSAGE = """**╔══❰ {mode} ❱══❍
║╭━➣
║┣⪼ 📊 **Progress:** {percentage}%
║┣
║┣⪼ {progress}
║┣
║┣⪼ **Done:** {finished} of {total}
║┣
║┣⪼ ⚡ **Speed:** {speed}/s
║┣
║┣⪼ ⏰ **ETA:** {eta}
║╰━➣
╚════════════════❍**"""
