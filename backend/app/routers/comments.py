from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import Pagination, get_current_user, get_db
from app.models.comment import CommentCreate, CommentPublic
from app.models.common import Page

router = APIRouter(prefix="/api", tags=["comments"])


async def _with_author_names(db: AsyncIOMotorDatabase, comments: list[dict]) -> list[dict]:
    user_ids = {comment["user_id"] for comment in comments}
    users_by_id = {}
    if user_ids:
        async for user in db.users.find({"_id": {"$in": list(user_ids)}}):
            users_by_id[user["_id"]] = user["name"]

    return [
        {**comment, "author_name": users_by_id.get(comment["user_id"], "알 수 없음")}
        for comment in comments
    ]


@router.post(
    "/books/{book_id}/comments",
    response_model=CommentPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    book_id: str,
    payload: CommentCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(book_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")

    doc = {
        "book_id": book["_id"],
        "user_id": current_user["_id"],
        "content": payload.content,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.comments.insert_one(doc)
    doc["_id"] = result.inserted_id

    (enriched,) = await _with_author_names(db, [doc])
    return enriched


@router.get("/books/{book_id}/comments", response_model=Page[CommentPublic])
async def list_comments(
    book_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    pagination: Annotated[Pagination, Depends(Pagination)],
):
    if not ObjectId.is_valid(book_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")

    query = {"book_id": ObjectId(book_id)}
    total = await db.comments.count_documents(query)
    cursor = (
        db.comments.find(query).sort("created_at", 1).skip(pagination.skip).limit(pagination.limit)
    )
    comments = await cursor.to_list(length=pagination.limit)
    items = await _with_author_names(db, comments)

    return Page(items=items, total=total, page=pagination.page, limit=pagination.limit)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(comment_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")

    comment = await db.comments.find_one({"_id": ObjectId(comment_id)})
    if comment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    if comment["user_id"] != current_user["_id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the comment owner")

    await db.comments.delete_one({"_id": comment["_id"]})
    return None
