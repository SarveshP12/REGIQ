"""Async MongoDB connection using Motor."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

settings = get_settings()

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_mongo() -> None:
    """Initialise the global Motor client & database reference."""
    global _client, _database
    _client = AsyncIOMotorClient(settings.mongo_url)
    _database = _client[settings.mongo_db]

    # Ensure indexes
    await _database.test_case_versions.create_index("test_case_id")
    await _database.test_case_versions.create_index([("test_case_id", 1), ("version", -1)])
    await _database.update_set_raw.create_index("change_set_id")
    await _database.notification_logs.create_index(
        "created_at", expireAfterSeconds=30 * 24 * 3600  # 30-day TTL
    )


async def close_mongo() -> None:
    """Close the Motor client."""
    global _client
    if _client:
        _client.close()


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Return the active MongoDB database handle."""
    if _database is None:
        raise RuntimeError("MongoDB not initialised – call connect_mongo() first")
    return _database
