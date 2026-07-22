from typing import Annotated

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import Pagination, get_current_user_optional, get_db
from app.models.common import Page
from app.models.feed import FeedItem
from app.models.review import Visibility
from app.services.enrichment import attach_author_and_likes

router = APIRouter(prefix="/api/feed", tags=["feed"])


@router.get("", response_model=Page[FeedItem])
async def get_feed(
    current_user: Annotated[dict | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    pagination: Annotated[Pagination, Depends(Pagination)],
    tag: str | None = None,
):
    query: dict = {"visibility": Visibility.PUBLIC.value}
    if tag:
        query["tags"] = tag

    total = await db.reviews.count_documents(query)
    cursor = (
        db.reviews.find(query).sort("created_at", -1).skip(pagination.skip).limit(pagination.limit)
    )
    reviews = await cursor.to_list(length=pagination.limit)

    current_user_id = current_user["_id"] if current_user else None
    enriched = await attach_author_and_likes(db, reviews, current_user_id)

    book_ids = list({review["book_id"] for review in reviews})
    books_by_id = {}
    if book_ids:
        async for book in db.books.find({"_id": {"$in": book_ids}}):
            books_by_id[book["_id"]] = book

    items = [
        {
            **review,
            "book": {
                "id": books_by_id[review["book_id"]]["_id"],
                "title": books_by_id[review["book_id"]]["title"],
                "cover_url": books_by_id[review["book_id"]].get("cover_url"),
            },
        }
        for review in enriched
        if review["book_id"] in books_by_id
    ]

    return Page(items=items, total=total, page=pagination.page, limit=pagination.limit)
