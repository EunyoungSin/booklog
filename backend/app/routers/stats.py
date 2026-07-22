from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, get_db
from app.models.stats import MonthlyStats

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _month_range(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start, end


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
