from pydantic import BaseModel


class LikeToggleResponse(BaseModel):
    liked: bool
    like_count: int
