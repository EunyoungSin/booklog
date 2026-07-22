from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import PyObjectId, RequiredTagList


class Visibility(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"


class ReviewCreate(BaseModel):
    book_id: str
    content: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)
    tags: RequiredTagList
    visibility: Visibility = Visibility.PUBLIC


class ReviewUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1)
    rating: int | None = Field(default=None, ge=1, le=5)
    tags: RequiredTagList | None = None
    visibility: Visibility | None = None


class ReviewPublic(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(validation_alias="_id")
    book_id: PyObjectId
    user_id: PyObjectId
    content: str
    rating: int
    tags: list[str]
    visibility: Visibility
    ai_summary: str | None = None
    ai_feedback: str | None = None
    ai_generated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ReviewWithAuthor(ReviewPublic):
    author_name: str
    like_count: int
    liked_by_me: bool
