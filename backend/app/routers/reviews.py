import logging
from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import Pagination, get_current_user, get_db
from app.models.common import Page
from app.models.like import LikeToggleResponse
from app.models.review import ReviewCreate, ReviewPublic, ReviewUpdate, Visibility
from app.services.gemini import GeminiAPIError, generate_review_ai_output

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


def _visible_or_404(review: dict | None, user_id: ObjectId) -> dict:
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    if review["visibility"] != Visibility.PUBLIC.value and review["user_id"] != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    return review


@router.post("", response_model=ReviewPublic, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(payload.book_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    book = await db.books.find_one({"_id": ObjectId(payload.book_id)})
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")

    now = datetime.now(timezone.utc)
    doc = {
        "book_id": book["_id"],
        "user_id": current_user["_id"],
        "content": payload.content,
        "rating": payload.rating,
        "tags": payload.tags,
        "visibility": payload.visibility.value,
        "ai_summary": None,
        "ai_feedback": None,
        "ai_generated_at": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.reviews.insert_one(doc)
    doc["_id"] = result.inserted_id

    # 독후감 저장 시 Gemini를 1회만 자동 호출한다. 실패해도 리뷰 생성 자체는 성공시키고,
    # 이후 사용자가 명시적으로 /ai-regenerate 를 호출했을 때만 재시도한다.
    try:
        ai_output = await generate_review_ai_output(payload.content, payload.rating)
    except GeminiAPIError as exc:
        logger.warning("Gemini auto-summary failed for a new review: %s", exc)
    else:
        ai_update = {
            "ai_summary": ai_output.summary,
            "ai_feedback": ai_output.feedback,
            "ai_generated_at": datetime.now(timezone.utc),
        }
        await db.reviews.update_one({"_id": doc["_id"]}, {"$set": ai_update})
        doc.update(ai_update)

    return doc


@router.get("", response_model=Page[ReviewPublic])
async def list_reviews(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    pagination: Annotated[Pagination, Depends(Pagination)],
    book_id: str | None = None,
    tag: str | None = None,
    mine: bool = False,
):
    query: dict = {}
    if book_id:
        if not ObjectId.is_valid(book_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
        query["book_id"] = ObjectId(book_id)
    if tag:
        query["tags"] = tag

    if mine:
        query["user_id"] = current_user["_id"]
    else:
        query["$or"] = [
            {"visibility": Visibility.PUBLIC.value},
            {"user_id": current_user["_id"]},
        ]

    total = await db.reviews.count_documents(query)
    cursor = (
        db.reviews.find(query).sort("created_at", -1).skip(pagination.skip).limit(pagination.limit)
    )
    items = await cursor.to_list(length=pagination.limit)
    return Page(items=items, total=total, page=pagination.page, limit=pagination.limit)


@router.get("/{review_id}", response_model=ReviewPublic)
async def get_review(
    review_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(review_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    return _visible_or_404(review, current_user["_id"])


@router.put("/{review_id}", response_model=ReviewPublic)
async def update_review(
    review_id: str,
    payload: ReviewUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(review_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    review = _visible_or_404(review, current_user["_id"])

    if review["user_id"] != current_user["_id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the review owner")

    update_fields: dict = {}
    if payload.content is not None:
        update_fields["content"] = payload.content
    if payload.rating is not None:
        update_fields["rating"] = payload.rating
    if payload.tags is not None:
        update_fields["tags"] = payload.tags
    if payload.visibility is not None:
        update_fields["visibility"] = payload.visibility.value

    if update_fields:
        update_fields["updated_at"] = datetime.now(timezone.utc)
        await db.reviews.update_one({"_id": review["_id"]}, {"$set": update_fields})
        review.update(update_fields)

    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(review_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    review = _visible_or_404(review, current_user["_id"])

    if review["user_id"] != current_user["_id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the review owner")

    await db.reviews.delete_one({"_id": review["_id"]})
    return None


@router.post("/{review_id}/ai-regenerate", response_model=ReviewPublic)
async def regenerate_ai_summary(
    review_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(review_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    review = _visible_or_404(review, current_user["_id"])

    if review["user_id"] != current_user["_id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the review owner")

    try:
        ai_output = await generate_review_ai_output(review["content"], review["rating"])
    except GeminiAPIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    ai_update = {
        "ai_summary": ai_output.summary,
        "ai_feedback": ai_output.feedback,
        "ai_generated_at": datetime.now(timezone.utc),
    }
    await db.reviews.update_one({"_id": review["_id"]}, {"$set": ai_update})
    review.update(ai_update)
    return review


@router.post("/{review_id}/like", response_model=LikeToggleResponse)
async def toggle_like(
    review_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(review_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    review = _visible_or_404(review, current_user["_id"])

    existing = await db.likes.find_one(
        {"review_id": review["_id"], "user_id": current_user["_id"]}
    )
    if existing is None:
        await db.likes.insert_one(
            {
                "review_id": review["_id"],
                "user_id": current_user["_id"],
                "created_at": datetime.now(timezone.utc),
            }
        )
        liked = True
    else:
        await db.likes.delete_one({"_id": existing["_id"]})
        liked = False

    like_count = await db.likes.count_documents({"review_id": review["_id"]})
    return LikeToggleResponse(liked=liked, like_count=like_count)


@router.get("/{review_id}/likes", response_model=LikeToggleResponse)
async def get_likes(
    review_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
):
    if not ObjectId.is_valid(review_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    review = _visible_or_404(review, current_user["_id"])

    like_count = await db.likes.count_documents({"review_id": review["_id"]})
    liked = (
        await db.likes.find_one({"review_id": review["_id"], "user_id": current_user["_id"]})
        is not None
    )
    return LikeToggleResponse(liked=liked, like_count=like_count)
