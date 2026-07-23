from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, get_db
from app.models.stats import CalendarDayBookInfo, CalendarDayReview, MonthlyStats

router = APIRouter(prefix="/api/stats", tags=["stats"])

SUMMARY_PREVIEW_LENGTH = 80


def _month_range(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start, end


def _year_range(year: int) -> tuple[datetime, datetime]:
    return datetime(year, 1, 1, tzinfo=timezone.utc), datetime(year + 1, 1, 1, tzinfo=timezone.utc)


def _day_range(day: date) -> tuple[datetime, datetime]:
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


async def _daily_review_counts(
    db: AsyncIOMotorDatabase, user_id: ObjectId, start: datetime, end: datetime
) -> dict[str, int]:
    pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": start, "$lt": end}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1},
            }
        },
    ]
    result = await db.reviews.aggregate(pipeline).to_list(length=None)
    return {row["_id"]: row["count"] for row in result}


def _summarize(review: dict) -> str:
    text = review.get("ai_summary") or review["content"]
    if len(text) <= SUMMARY_PREVIEW_LENGTH:
        return text
    return text[:SUMMARY_PREVIEW_LENGTH].rstrip() + "..."


@router.get("/monthly", response_model=MonthlyStats)
async def get_monthly_stats(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    year: Annotated[int | None, Query(ge=1900, le=2100)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
):
    if (year is None) != (month is None):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "year and month must be provided together")

    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month

    start, end = _month_range(year, month)

    books_added_count = await db.user_books.count_documents(
        {"user_id": current_user["_id"], "added_at": {"$gte": start, "$lt": end}}
    )

    review_query = {
        "user_id": current_user["_id"],
        "created_at": {"$gte": start, "$lt": end},
    }
    reviews_written_count = await db.reviews.count_documents(review_query)

    average_rating = None
    if reviews_written_count > 0:
        pipeline = [
            {"$match": review_query},
            {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}},
        ]
        result = await db.reviews.aggregate(pipeline).to_list(length=1)
        if result:
            average_rating = round(result[0]["avg_rating"], 2)

    return MonthlyStats(
        year=year,
        month=month,
        books_added_count=books_added_count,
        reviews_written_count=reviews_written_count,
        average_rating=average_rating,
    )


@router.get("/calendar", response_model=dict[str, int])
async def get_calendar_month(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    year: Annotated[int, Query(ge=1900, le=2100)],
    month: Annotated[int, Query(ge=1, le=12)],
):
    start, end = _month_range(year, month)
    return await _daily_review_counts(db, current_user["_id"], start, end)


@router.get("/calendar/year", response_model=dict[str, int])
async def get_calendar_year(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    year: Annotated[int, Query(ge=1900, le=2100)],
):
    start, end = _year_range(year)
    return await _daily_review_counts(db, current_user["_id"], start, end)


@router.get("/calendar/day", response_model=list[CalendarDayReview])
async def get_calendar_day(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    date: Annotated[date, Query()],
):
    start, end = _day_range(date)
    cursor = (
        db.reviews.find({"user_id": current_user["_id"], "created_at": {"$gte": start, "$lt": end}})
        .sort("created_at", -1)
    )
    reviews = await cursor.to_list(length=None)

    book_ids = list({review["book_id"] for review in reviews})
    books_by_id = {}
    if book_ids:
        async for book in db.books.find({"_id": {"$in": book_ids}}):
            books_by_id[book["_id"]] = book

    return [
        CalendarDayReview(
            id=str(review["_id"]),
            book=CalendarDayBookInfo(
                id=str(books_by_id[review["book_id"]]["_id"]),
                title=books_by_id[review["book_id"]]["title"],
            ),
            rating=review["rating"],
            summary_preview=_summarize(review),
            created_at=review["created_at"],
        )
        for review in reviews
        if review["book_id"] in books_by_id
    ]
