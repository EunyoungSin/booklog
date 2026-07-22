from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import PyObjectId


class BookSearchResult(BaseModel):
    title: str
    author: str | None = None
    isbn: str | None = None
    cover_url: str | None = None
    publisher: str | None = None
    description: str | None = None
    pub_date: str | None = None


class BookRegisterRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    author: str | None = Field(default=None, max_length=300)
    isbn: str | None = Field(default=None, max_length=20)
    cover_url: str | None = None
    publisher: str | None = Field(default=None, max_length=200)
    description: str | None = None


class BookPublic(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(validation_alias="_id")
    title: str
    author: str | None = None
    isbn: str | None = None
    cover_url: str | None = None
    publisher: str | None = None
    description: str | None = None
    added_by: PyObjectId
    created_at: datetime


class LibraryItem(BaseModel):
    book: BookPublic
    added_at: datetime
