from pydantic import BaseModel

from app.models.common import PyObjectId
from app.models.review import ReviewWithAuthor


class FeedBookInfo(BaseModel):
    id: PyObjectId
    title: str
    cover_url: str | None = None


class FeedItem(ReviewWithAuthor):
    book: FeedBookInfo
