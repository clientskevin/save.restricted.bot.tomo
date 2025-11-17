import os
from dotenv import load_dotenv
from pyrogram.enums import MessageMediaType
from pyrogram.client import Client
from bot.enums import CaptionVariables
from typing_extensions import Annotated

if os.path.exists("config.env"):
    load_dotenv(".env")
else:
    load_dotenv()


def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default


class Config(object):
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "tg_bot")
    DATABASE_URL = os.environ.get("DATABASE_URL", None)
    OWNER_ID = os.environ.get("OWNER_ID")

    # LOG CHANNELS
    FILES_LOG = int(os.environ.get("FILES_LOG", 0))
    ON_MESSAGE_SOURCE: Annotated[int, "Messages posted on this channels are instantly forwarded to dest"] = int(os.environ.get("ON_MESSAGE_SOURCE", 0))


    # Optional
    WEB_SERVER = is_enabled(os.environ.get("WEB_SERVER", "False"), False)
    SLEEP_TIME = int(os.environ.get("SLEEP_TIME", 60))

    # Operator
    CLIENTS = {}
    TRANSFERS = {}

    ALL_MEDIA_TYPES = {
        MessageMediaType.PHOTO.value: "📷 Photo",
        MessageMediaType.VIDEO.value: "🎥 Video", 
        MessageMediaType.AUDIO.value: "🎵 Audio",
        MessageMediaType.DOCUMENT.value: "📄 Document",
        "text": "📄 Text",
    }

    if OWNER_ID.isdigit():
        OWNER_ID = int(OWNER_ID)

class ContextVariables(object):
    BOT: Client = None

class Script(object):

    START_MESSAGE = """💾 **Welcome to the Ultimate Content Saver Bot on Telegram!** 💾

**Steps to Get Started:**
1. **Log in** to your account by sending /account along with your Phone number. 🔑  
2. **Send me any message link**, and I’ll safely store it for you! 🗂️  
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
