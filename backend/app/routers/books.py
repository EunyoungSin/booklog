from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import Pagination, get_current_user, get_current_user_optional, get_db
from app.models.book import BookPublic, BookRegisterRequest, BookSearchResult, LibraryItem
from app.models.common import Page
from app.models.review import ReviewWithAuthor, Visibility
from app.services.aladin import AladinAPIError, search_books
from app.services.enrichment import attach_author_and_likes

router = APIRouter(prefix="/api", tags=["books"])


@router.get("/books/search", response_model=list[BookSearchResult])
async def search(
    query: Annotated[str, Query(min_length=1)],
    max_results: Annotated[int, Query(ge=1, le=50)] = 20,
):
    try:
        return await search_books(query, max_results)
    except AladinAPIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc


@router.post("/books", response_model=BookPublic, status_code=status.HTTP_201_CREATED)
async def register_book(
    payload: BookRegisterRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    book_doc = None
    if payload.isbn:
        book_doc = await db.books.find_one({"isbn": payload.isbn})

    if book_doc is None:
        new_book = {
            "title": payload.title,
            "author": payload.author,
            "cover_url": payload.cover_url,
            "publisher": payload.publisher,
            "description": payload.description,
            "added_by": current_user["_id"],
            "created_at": datetime.now(timezone.utc),
        }
        # Omit "isbn" entirely (rather than setting it to None) when there is no
        # ISBN. The unique index on "isbn" is sparse, but MongoDB sparse indexes
        # only skip documents where the field is truly absent — a field that is
        # merely present with a null value still gets indexed, so every
        # isbn-less book beyond the first would collide on isbn: null.
        if payload.isbn:
            new_book["isbn"] = payload.isbn
        result = await db.books.insert_one(new_book)
        book_doc = {**new_book, "_id": result.inserted_id}

    await db.user_books.update_one(
        {"user_id": current_user["_id"], "book_id": book_doc["_id"]},
        {"$setOnInsert": {"added_at": datetime.now(timezone.utc)}},
        upsert=True,
    )

    return book_doc


@router.get("/library/me", response_model=Page[LibraryItem])
async def get_my_library(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    pagination: Annotated[Pagination, Depends(Pagination)],
):
    query = {"user_id": current_user["_id"]}
    total = await db.user_books.count_documents(query)

    cursor = (
        db.user_books.find(query)
        .sort("added_at", -1)
        .skip(pagination.skip)
        .limit(pagination.limit)
    )
    user_books = await cursor.to_list(length=pagination.limit)

    book_ids = [ub["book_id"] for ub in user_books]
    books_by_id = {}
    if book_ids:
        async for book in db.books.find({"_id": {"$in": book_ids}}):
            books_by_id[book["_id"]] = book

    items = [
        LibraryItem(book=books_by_id[ub["book_id"]], added_at=ub["added_at"])
        for ub in user_books
        if ub["book_id"] in books_by_id
    ]

    return Page(items=items, total=total, page=pagination.page, limit=pagination.limit)


@router.get("/books/{book_id}", response_model=BookPublic)
async def get_book(
    book_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(book_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")

    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")

    return book


@router.get("/books/{book_id}/reviews", response_model=Page[ReviewWithAuthor])
async def get_book_public_reviews(
    book_id: str,
    current_user: Annotated[dict | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    pagination: Annotated[Pagination, Depends(Pagination)],
):
    if not ObjectId.is_valid(book_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")

    query = {"book_id": book["_id"], "visibility": Visibility.PUBLIC.value}
    total = await db.reviews.count_documents(query)
    cursor = (
        db.reviews.find(query).sort("created_at", -1).skip(pagination.skip).limit(pagination.limit)
    )
    reviews = await cursor.to_list(length=pagination.limit)
    current_user_id = current_user["_id"] if current_user else None
    items = await attach_author_and_likes(db, reviews, current_user_id)

    return Page(items=items, total=total, page=pagination.page, limit=pagination.limit)


@router.delete("/library/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_library(
    book_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(book_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found in your library")

    result = await db.user_books.delete_one(
        {"user_id": current_user["_id"], "book_id": ObjectId(book_id)}
    )
    if result.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found in your library")

    return None
