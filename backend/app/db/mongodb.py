import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database is not connected yet. Did startup run?")
    return _db


async def connect_to_mongo() -> None:
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    _db = _client[settings.mongodb_db_name]
    await _create_indexes(_db)
    logger.info("Connected to MongoDB database '%s'", settings.mongodb_db_name)


async def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed")


async def _create_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index("email", unique=True)

    await db.refresh_tokens.create_index("token_hash", unique=True)
    await db.refresh_tokens.create_index("user_id")
    await db.refresh_tokens.create_index("expires_at", expireAfterSeconds=0)

    await db.email_verification_codes.create_index("email", unique=True)
    await db.email_verification_codes.create_index("expires_at", expireAfterSeconds=0)

    await db.books.create_index("isbn", unique=True, sparse=True)
    await db.books.create_index("title")

    await db.user_books.create_index([("user_id", 1), ("book_id", 1)], unique=True)

    await db.reviews.create_index([("book_id", 1), ("visibility", 1), ("created_at", -1)])
    await db.reviews.create_index([("user_id", 1), ("created_at", -1)])
    await db.reviews.create_index("tags")
    await db.reviews.create_index([("content", "text"), ("tags", "text")])

    await db.quotes.create_index([("book_id", 1), ("created_at", -1)])
    await db.quotes.create_index([("user_id", 1)])
    await db.quotes.create_index("tags")
    await db.quotes.create_index([("text", "text"), ("tags", "text")])

    await db.comments.create_index([("book_id", 1), ("created_at", 1)])

    await db.likes.create_index([("review_id", 1), ("user_id", 1)], unique=True)
