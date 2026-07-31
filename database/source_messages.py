from datetime import datetime
from typing import List, Optional

from database.core import Core

MAX_SOURCE_MESSAGES = 10000
TEXT_MAX_LEN = 200


class SourceMessagesDB(Core):
    """Temp store of recent source channel messages (text/caption + link)."""

    def __init__(self, uri, database_name):
        super().__init__(uri, database_name, "source_messages")
        self._indexes_ready = False

    async def _ensure_indexes(self):
        if self._indexes_ready:
            return
        await self.col.create_index(
            [("source_id", 1), ("message_id", 1)], unique=True
        )
        await self.col.create_index([("created_at", 1)])
        self._indexes_ready = True

    async def save_message(self, source_id: int, message_id: int, link: str, text: str):
        """
        Upsert by (source_id, message_id) to avoid duplicates.
        Keeps only the newest MAX_SOURCE_MESSAGES documents.
        """
        await self._ensure_indexes()
        now = datetime.now()
        await self.col.update_one(
            {"source_id": source_id, "message_id": message_id},
            {
                "$set": {
                    "link": link,
                    "text": (text or "")[:TEXT_MAX_LEN],
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "source_id": source_id,
                    "message_id": message_id,
                    "created_at": now,
                    "forwards": [],
                },
            },
            upsert=True,
        )
        await self._trim_to_limit()

    async def add_forward(
        self,
        source_id: int,
        message_id: int,
        dest_id: int,
        dest_message_id: int,
    ):
        """Record a destination copy of a source message."""
        await self._ensure_indexes()
        await self.col.update_one(
            {"source_id": source_id, "message_id": message_id},
            {
                "$addToSet": {
                    "forwards": {
                        "dest_id": dest_id,
                        "dest_message_id": dest_message_id,
                    }
                },
                "$set": {"updated_at": datetime.now()},
                "$setOnInsert": {
                    "source_id": source_id,
                    "message_id": message_id,
                    "link": "",
                    "text": "",
                    "created_at": datetime.now(),
                },
            },
            upsert=True,
        )
        await self._trim_to_limit()

    async def get_message(
        self, source_id: int, message_id: int
    ) -> Optional[dict]:
        await self._ensure_indexes()
        return await self.col.find_one(
            {"source_id": source_id, "message_id": message_id}
        )

    async def get_messages(
        self, source_id: int, message_ids: List[int]
    ) -> List[dict]:
        await self._ensure_indexes()
        return await self.col.find(
            {"source_id": source_id, "message_id": {"$in": message_ids}}
        ).to_list(length=len(message_ids))

    async def remove_message(self, source_id: int, message_id: int):
        await self._ensure_indexes()
        return await self.col.delete_one(
            {"source_id": source_id, "message_id": message_id}
        )

    async def _trim_to_limit(self):
        count = await self.col.count_documents({})
        if count <= MAX_SOURCE_MESSAGES:
            return

        excess = count - MAX_SOURCE_MESSAGES
        oldest = (
            await self.col.find({}, {"_id": 1})
            .sort("created_at", 1)
            .limit(excess)
            .to_list(length=excess)
        )
        if oldest:
            await self.col.delete_many({"_id": {"$in": [doc["_id"] for doc in oldest]}})
