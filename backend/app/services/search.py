import re

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _regex(q: str) -> dict:
    return {"$regex": re.escape(q), "$options": "i"}


def make_snippet(text: str, length: int = 140) -> str:
    text = text.strip().replace("\n", " ")
    return text if len(text) <= length else text[:length].rstrip() + "…"


async def _try_atlas_search(
    db: AsyncIOMotorDatabase,
    collection: str,
    path: list[str],
    q: str,
    extra_match: dict | None,
    skip: int,
    limit: int,
) -> list[dict] | None:
    """Attempt an Atlas Search ($search) query; return None if unavailable so the
    caller can fall back to a regex scan. This covers local MongoDB, mongomock in
    tests, and a fresh Atlas M0 cluster that hasn't had a Search index created yet.
    """
    pipeline: list[dict] = [{"$search": {"index": "default", "text": {"query": q, "path": path}}}]
    if extra_match:
        pipeline.append({"$match": extra_match})
    pipeline.extend([{"$skip": skip}, {"$limit": limit}])
    try:
        return await db[collection].aggregate(pipeline).to_list(length=limit)
    except Exception:
        return None


async def search_books(db: AsyncIOMotorDatabase, q: str, skip: int, limit: int) -> list[dict]:
    docs = await _try_atlas_search(db, "books", ["title", "author"], q, None, skip, limit)
    if docs is not None:
        return docs
    cursor = (
        db.books.find({"$or": [{"title": _regex(q)}, {"author": _regex(q)}]})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)


async def count_books(db: AsyncIOMotorDatabase, q: str) -> int:
    return await db.books.count_documents({"$or": [{"title": _regex(q)}, {"author": _regex(q)}]})


def _review_visibility_filter(user_id: ObjectId | None) -> dict:
    if user_id is None:
        return {"visibility": "public"}
    return {"$or": [{"visibility": "public"}, {"user_id": user_id}]}


async def search_reviews(
    db: AsyncIOMotorDatabase, q: str, user_id: ObjectId | None, skip: int, limit: int
) -> list[dict]:
    visibility_filter = _review_visibility_filter(user_id)
    docs = await _try_atlas_search(
        db, "reviews", ["content", "tags"], q, visibility_filter, skip, limit
    )
    if docs is not None:
        return docs
    cursor = (
        db.reviews.find(
            {"$and": [{"$or": [{"content": _regex(q)}, {"tags": _regex(q)}]}, visibility_filter]}
        )
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)


async def count_reviews(db: AsyncIOMotorDatabase, q: str, user_id: ObjectId | None) -> int:
    visibility_filter = _review_visibility_filter(user_id)
    return await db.reviews.count_documents(
        {"$and": [{"$or": [{"content": _regex(q)}, {"tags": _regex(q)}]}, visibility_filter]}
    )


async def search_quotes(
    db: AsyncIOMotorDatabase, q: str, user_id: ObjectId | None, skip: int, limit: int
) -> list[dict]:
    # 인용문은 항상 소유자 본인만 검색 대상 (4단계에서 정한 quotes 비공개 정책과 동일).
    # 로그인하지 않은 사용자는 소유자가 없으므로 검색 결과도 없다.
    if user_id is None:
        return []
    owner_filter = {"user_id": user_id}
    docs = await _try_atlas_search(db, "quotes", ["text", "tags"], q, owner_filter, skip, limit)
    if docs is not None:
        return docs
    cursor = (
        db.quotes.find({"$and": [{"$or": [{"text": _regex(q)}, {"tags": _regex(q)}]}, owner_filter]})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)


async def count_quotes(db: AsyncIOMotorDatabase, q: str, user_id: ObjectId | None) -> int:
    if user_id is None:
        return 0
    return await db.quotes.count_documents(
        {"$and": [{"$or": [{"text": _regex(q)}, {"tags": _regex(q)}]}, {"user_id": user_id}]}
    )
