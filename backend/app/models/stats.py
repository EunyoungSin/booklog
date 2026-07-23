from datetime import datetime

from pydantic import BaseModel

from app.models.common import PyObjectId


class MonthlyStats(BaseModel):
    year: int
    month: int
    books_added_count: int
    reviews_written_count: int
    average_rating: float | None = None


class CalendarDayBookInfo(BaseModel):
    id: PyObjectId
    title: str


class CalendarDayReview(BaseModel):
    id: PyObjectId
    book: CalendarDayBookInfo
    rating: int
    summary_preview: str
    created_at: datetime
