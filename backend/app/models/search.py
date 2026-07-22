from enum import StrEnum

from pydantic import BaseModel


class SearchResultType(StrEnum):
    BOOK = "book"
    REVIEW = "review"
    QUOTE = "quote"


class SearchResultItem(BaseModel):
    type: SearchResultType
    id: str
    book_id: str | None = None
    title: str
    snippet: str | None = None
