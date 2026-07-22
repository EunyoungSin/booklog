from datetime import datetime, timezone

from bson import ObjectId


async def _get_user_id(client, headers) -> ObjectId:
    res = await client.get("/api/auth/me", headers=headers)
    return ObjectId(res.json()["id"])


async def test_monthly_stats_for_specific_past_month(client, auth_headers, db, book_id):
    user_id = await _get_user_id(client, auth_headers)
    book_oid = ObjectId(book_id)

    # seed a March 2025 book addition and two reviews directly (bypassing "now")
    march = datetime(2025, 3, 15, tzinfo=timezone.utc)
    await db.user_books.insert_one(
        {"user_id": user_id, "book_id": ObjectId(), "added_at": march}
    )
    await db.reviews.insert_many(
        [
            {
                "book_id": book_oid,
                "user_id": user_id,
                "content": "a",
                "rating": 4,
                "tags": [],
                "visibility": "public",
                "ai_summary": None,
                "ai_feedback": None,
                "ai_generated_at": None,
                "created_at": march,
                "updated_at": march,
            },
            {
                "book_id": book_oid,
                "user_id": user_id,
                "content": "b",
                "rating": 2,
                "tags": [],
                "visibility": "private",
                "ai_summary": None,
                "ai_feedback": None,
                "ai_generated_at": None,
                "created_at": march,
                "updated_at": march,
            },
        ]
    )
    # a review in a different month should not count
    april = datetime(2025, 4, 1, tzinfo=timezone.utc)
    await db.reviews.insert_one(
        {
            "book_id": book_oid,
            "user_id": user_id,
            "content": "c",
            "rating": 5,
            "tags": [],
            "visibility": "public",
            "ai_summary": None,
            "ai_feedback": None,
            "ai_generated_at": None,
            "created_at": april,
            "updated_at": april,
        }
    )

    res = await client.get(
        "/api/stats/monthly", params={"year": 2025, "month": 3}, headers=auth_headers
    )
    assert res.status_code == 200
    body = res.json()
    assert body["year"] == 2025
    assert body["month"] == 3
    assert body["books_added_count"] == 1
    assert body["reviews_written_count"] == 2
    assert body["average_rating"] == 3.0


async def test_monthly_stats_no_data_returns_zero_and_null_average(client, auth_headers):
    res = await client.get(
        "/api/stats/monthly", params={"year": 1999, "month": 1}, headers=auth_headers
    )
    body = res.json()
    assert body["books_added_count"] == 0
    assert body["reviews_written_count"] == 0
    assert body["average_rating"] is None


async def test_monthly_stats_defaults_to_current_month(client, auth_headers, book_id):
    await client.post(
        "/api/reviews",
        json={"book_id": book_id, "content": "지금 쓴 리뷰", "rating": 5, "tags": ["일반"], "visibility": "public"},
        headers=auth_headers,
    )

    res = await client.get("/api/stats/monthly", headers=auth_headers)
    body = res.json()
    assert body["reviews_written_count"] >= 1
    assert body["books_added_count"] >= 1  # book_id fixture registers a book "now"


async def test_monthly_stats_requires_both_year_and_month(client, auth_headers):
    res = await client.get("/api/stats/monthly", params={"year": 2025}, headers=auth_headers)
    assert res.status_code == 400
