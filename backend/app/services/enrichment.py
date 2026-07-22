from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def attach_author_and_likes(
    db: AsyncIOMotorDatabase, reviews: list[dict], current_user_id: ObjectId | None
) -> list[dict]:
    """Enrich raw review documents with author_name, like_count and liked_by_me."""
    if not reviews:
        return []

    user_ids = list({review["user_id"] for review in reviews})
    review_ids = [review["_id"] for review in reviews]

    users_by_id: dict[ObjectId, str] = {}
    async for user in db.users.find({"_id": {"$in": user_ids}}):
        users_by_id[user["_id"]] = user["name"]

    like_counts: dict[ObjectId, int] = {}
    my_likes: set[ObjectId] = set()
    async for like in db.likes.find({"review_id": {"$in": review_ids}}):
        like_counts[like["review_id"]] = like_counts.get(like["review_id"], 0) + 1
        if like["user_id"] == current_user_id:
            my_likes.add(like["review_id"])

    return [
        {
            **review,
            "author_name": users_by_id.get(review["user_id"], "알 수 없음"),
            "like_count": like_counts.get(review["_id"], 0),
            "liked_by_me": review["_id"] in my_likes,
        }
        for review in reviews
    ]
