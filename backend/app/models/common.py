from typing import Annotated, Any, Generic, TypeVar

from bson import ObjectId
from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(str)]

T = TypeVar("T")


def _normalize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    for tag in tags:
        tag = tag.strip()
        if tag and tag not in normalized:
            normalized.append(tag)
    return normalized


TagList = Annotated[list[str], AfterValidator(_normalize_tags)]


def _require_at_least_one_tag(tags: list[str]) -> list[str]:
    if not tags:
        raise ValueError("최소 1개 이상의 태그를 입력해야 합니다.")
    return tags


RequiredTagList = Annotated[
    list[str], AfterValidator(_normalize_tags), AfterValidator(_require_at_least_one_tag)
]


def validate_object_id(value: Any) -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    if ObjectId.is_valid(value):
        return ObjectId(value)
    raise ValueError(f"'{value}' is not a valid ObjectId")


class MongoBaseModel(BaseModel):
    """Base for response models that read documents straight from MongoDB."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId = Field(validation_alias="_id")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int
