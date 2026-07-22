from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import Pagination, get_current_user, get_db
from app.models.common import Page
from app.models.quote import QuoteCreate, QuotePublic, QuoteUpdate

router = APIRouter(prefix="/api/quotes", tags=["quotes"])


def _owned_or_404(quote: dict | None, user_id: ObjectId) -> dict:
    if quote is None or quote["user_id"] != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quote not found")
    return quote


@router.post("", response_model=QuotePublic, status_code=status.HTTP_201_CREATED)
async def create_quote(
    payload: QuoteCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(payload.book_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    book = await db.books.find_one({"_id": ObjectId(payload.book_id)})
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")

    doc = {
        "book_id": book["_id"],
        "user_id": current_user["_id"],
        "text": payload.text,
        "page": payload.page,
        "tags": payload.tags,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.quotes.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


@router.get("", response_model=Page[QuotePublic])
async def list_quotes(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    pagination: Annotated[Pagination, Depends(Pagination)],
    book_id: str | None = None,
    tag: str | None = None,
):
    # 인용문은 소유자 본인에게만 노출됩니다 (books/reviews와 달리 공개 개념이 없는 개인 기록).
    query: dict = {"user_id": current_user["_id"]}
    if book_id:
        if not ObjectId.is_valid(book_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
        query["book_id"] = ObjectId(book_id)
    if tag:
        query["tags"] = tag

    total = await db.quotes.count_documents(query)
    cursor = (
        db.quotes.find(query).sort("created_at", -1).skip(pagination.skip).limit(pagination.limit)
    )
    items = await cursor.to_list(length=pagination.limit)
    return Page(items=items, total=total, page=pagination.page, limit=pagination.limit)


@router.get("/{quote_id}", response_model=QuotePublic)
async def get_quote(
    quote_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(quote_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quote not found")
    quote = await db.quotes.find_one({"_id": ObjectId(quote_id)})
    return _owned_or_404(quote, current_user["_id"])


@router.put("/{quote_id}", response_model=QuotePublic)
async def update_quote(
    quote_id: str,
    payload: QuoteUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(quote_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quote not found")
    quote = await db.quotes.find_one({"_id": ObjectId(quote_id)})
    quote = _owned_or_404(quote, current_user["_id"])

    update_fields: dict = {}
    if payload.text is not None:
        update_fields["text"] = payload.text
    if payload.page is not None:
        update_fields["page"] = payload.page
    if payload.tags is not None:
        update_fields["tags"] = payload.tags

    if update_fields:
        await db.quotes.update_one({"_id": quote["_id"]}, {"$set": update_fields})
        quote.update(update_fields)

    return quote


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(quote_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quote not found")
    quote = await db.quotes.find_one({"_id": ObjectId(quote_id)})
    quote = _owned_or_404(quote, current_user["_id"])

    await db.quotes.delete_one({"_id": quote["_id"]})
    return None
