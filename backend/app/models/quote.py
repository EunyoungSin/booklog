from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import PyObjectId, RequiredTagList


class QuoteCreate(BaseModel):
    book_id: str
    text: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    tags: RequiredTagList


class QuoteUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1)
    page: int | None = Field(default=None, ge=1)
    tags: RequiredTagList | None = None


class QuotePublic(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(validation_alias="_id")
    book_id: PyObjectId
    user_id: PyObjectId
    text: str
    page: int | None = None
    tags: list[str]
    created_at: datetime
