from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import PyObjectId


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentPublic(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(validation_alias="_id")
    book_id: PyObjectId
    user_id: PyObjectId
    author_name: str
    content: str
    created_at: datetime
