from enum import StrEnum
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import Pagination, get_current_user_optional, get_db
from app.models.common import Page
from app.models.search import SearchResultItem, SearchResultType
from app.services.search import (
    count_books,
    count_quotes,
    count_reviews,
    make_snippet,
    search_books,
    search_quotes,
    search_reviews,
)

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchScope(StrEnum):
    ALL = "all"
    BOOKS = "books"
    REVIEWS = "reviews"
    QUOTES = "quotes"


async def _load_books(book_ids: set[ObjectId], db: AsyncIOMotorDatabase) -> dict:
    books_by_id: dict = {}
    if book_ids:
        async for book in db.books.find({"_id": {"$in": list(book_ids)}}):
            books_by_id[book["_id"]] = book
    return books_by_id


def _book_to_item(book: dict) -> SearchResultItem:
    return SearchResultItem(
        type=SearchResultType.BOOK,
        id=str(book["_id"]),
        book_id=str(book["_id"]),
        title=book["title"],
        snippet=book.get("author"),
    )


def _review_to_item(review: dict, books_by_id: dict) -> SearchResultItem:
    book = books_by_id.get(review["book_id"])
    return SearchResultItem(
        type=SearchResultType.REVIEW,
        id=str(review["_id"]),
        book_id=str(review["book_id"]),
        title=book["title"] if book else "알 수 없는 도서",
        snippet=make_snippet(review["content"]),
    )


def _quote_to_item(quote: dict, books_by_id: dict) -> SearchResultItem:
    book = books_by_id.get(quote["book_id"])
    return SearchResultItem(
        type=SearchResultType.QUOTE,
        id=str(quote["_id"]),
        book_id=str(quote["book_id"]),
        title=book["title"] if book else "알 수 없는 도서",
        snippet=make_snippet(quote["text"]),
    )


@router.get("", response_model=Page[SearchResultItem])
async def search(
    q: Annotated[str, Query(min_length=1)],
    current_user: Annotated[dict | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    pagination: Annotated[Pagination, Depends(Pagination)],
    type: SearchScope = SearchScope.ALL,
):
    user_id = current_user["_id"] if current_user else None

    if type == SearchScope.BOOKS:
        docs = await search_books(db, q, pagination.skip, pagination.limit)
        total = await count_books(db, q)
        items = [_book_to_item(book) for book in docs]
        return Page(items=items, total=total, page=pagination.page, limit=pagination.limit)

    if type == SearchScope.REVIEWS:
        docs = await search_reviews(db, q, user_id, pagination.skip, pagination.limit)
        total = await count_reviews(db, q, user_id)
        books_by_id = await _load_books({d["book_id"] for d in docs}, db)
        items = [_review_to_item(review, books_by_id) for review in docs]
        return Page(items=items, total=total, page=pagination.page, limit=pagination.limit)

    if type == SearchScope.QUOTES:
        docs = await search_quotes(db, q, user_id, pagination.skip, pagination.limit)
        total = await count_quotes(db, q, user_id)
        books_by_id = await _load_books({d["book_id"] for d in docs}, db)
        items = [_quote_to_item(quote, books_by_id) for quote in docs]
        return Page(items=items, total=total, page=pagination.page, limit=pagination.limit)

    # type == ALL: best-effort merge across the three categories. Each category is
    # over-fetched up to (page * limit), concatenated (books, then reviews, then
    # quotes), and sliced in Python — this is not a globally relevance-ranked merge,
    # but it's a reasonable MVP behavior at MongoDB Atlas M0 scale.
    fetch_cap = min(pagination.page * pagination.limit, 100)
    books_docs = await search_books(db, q, 0, fetch_cap)
    reviews_docs = await search_reviews(db, q, user_id, 0, fetch_cap)
    quotes_docs = await search_quotes(db, q, user_id, 0, fetch_cap)

    book_ids_needed = {r["book_id"] for r in reviews_docs} | {qd["book_id"] for qd in quotes_docs}
    books_by_id = await _load_books(book_ids_needed, db)

    all_items = (
        [_book_to_item(book) for book in books_docs]
        + [_review_to_item(review, books_by_id) for review in reviews_docs]
        + [_quote_to_item(quote, books_by_id) for quote in quotes_docs]
    )

    total = (
        await count_books(db, q)
        + await count_reviews(db, q, user_id)
        + await count_quotes(db, q, user_id)
    )

    page_items = all_items[pagination.skip : pagination.skip + pagination.limit]
    return Page(items=page_items, total=total, page=pagination.page, limit=pagination.limit)
