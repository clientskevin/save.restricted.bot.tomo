from bot.config import settings

from .config import ConfigDB
from .transfers import TransfersDB
from .user_channels import UserChannelDatabase
from .users import UserDatabase


class Database:
    def __init__(self):
        self.users = UserDatabase(settings.DATABASE_URL, settings.DATABASE_NAME)
        self.config = ConfigDB(settings.DATABASE_URL, settings.DATABASE_NAME)
        self.user_channels = UserChannelDatabase(
            settings.DATABASE_URL, settings.DATABASE_NAME
        )
        self.transfers = TransfersDB(settings.DATABASE_URL, settings.DATABASE_NAME)


db = Database()
