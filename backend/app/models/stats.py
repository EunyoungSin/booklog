from pydantic import BaseModel


class MonthlyStats(BaseModel):
    year: int
    month: int
    books_added_count: int
    reviews_written_count: int
    average_rating: float | None = None
