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


def _review_doc(user_id, book_id, created_at, **overrides):
    doc = {
        "book_id": book_id,
        "user_id": user_id,
        "content": "내용",
        "rating": 4,
        "tags": [],
        "visibility": "public",
        "ai_summary": None,
        "ai_feedback": None,
        "ai_generated_at": None,
        "created_at": created_at,
        "updated_at": created_at,
    }
    doc.update(overrides)
    return doc


async def test_calendar_month_groups_counts_by_day(client, auth_headers, db, book_id):
    user_id = await _get_user_id(client, auth_headers)
    book_oid = ObjectId(book_id)

    await db.reviews.insert_many(
        [
            _review_doc(user_id, book_oid, datetime(2026, 7, 1, 9, tzinfo=timezone.utc)),
            _review_doc(user_id, book_oid, datetime(2026, 7, 1, 20, tzinfo=timezone.utc)),
            _review_doc(user_id, book_oid, datetime(2026, 7, 3, tzinfo=timezone.utc)),
            # different month, should not count
            _review_doc(user_id, book_oid, datetime(2026, 8, 1, tzinfo=timezone.utc)),
        ]
    )

    res = await client.get(
        "/api/stats/calendar", params={"year": 2026, "month": 7}, headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json() == {"2026-07-01": 2, "2026-07-03": 1}


async def test_calendar_month_excludes_other_users_reviews(
    client, auth_headers, other_auth_headers, db, book_id
):
    other_user_id = await _get_user_id(client, other_auth_headers)
    book_oid = ObjectId(book_id)

    await db.reviews.insert_one(
        _review_doc(other_user_id, book_oid, datetime(2026, 7, 1, tzinfo=timezone.utc))
    )

    res = await client.get(
        "/api/stats/calendar", params={"year": 2026, "month": 7}, headers=auth_headers
    )
    assert res.json() == {}


async def test_calendar_year_covers_whole_year(client, auth_headers, db, book_id):
    user_id = await _get_user_id(client, auth_headers)
    book_oid = ObjectId(book_id)

    await db.reviews.insert_many(
        [
            _review_doc(user_id, book_oid, datetime(2026, 1, 5, tzinfo=timezone.utc)),
            _review_doc(user_id, book_oid, datetime(2026, 12, 31, tzinfo=timezone.utc)),
            _review_doc(user_id, book_oid, datetime(2025, 12, 31, tzinfo=timezone.utc)),
        ]
    )

    res = await client.get("/api/stats/calendar/year", params={"year": 2026}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == {"2026-01-05": 1, "2026-12-31": 1}


async def test_calendar_day_returns_reviews_with_book_and_preview(client, auth_headers, db, book_id):
    user_id = await _get_user_id(client, auth_headers)
    book_oid = ObjectId(book_id)

    await db.reviews.insert_one(
        _review_doc(
            user_id,
            book_oid,
            datetime(2026, 7, 1, 9, tzinfo=timezone.utc),
            content="가" * 100,
            rating=5,
        )
    )

    res = await client.get(
        "/api/stats/calendar/day", params={"date": "2026-07-01"}, headers=auth_headers
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["book"]["id"] == book_id
    assert body[0]["book"]["title"] == "채식주의자"
    assert body[0]["rating"] == 5
    assert body[0]["summary_preview"] == "가" * 80 + "..."


async def test_calendar_day_prefers_ai_summary_for_preview(client, auth_headers, db, book_id):
    user_id = await _get_user_id(client, auth_headers)
    book_oid = ObjectId(book_id)

    await db.reviews.insert_one(
        _review_doc(
            user_id,
            book_oid,
            datetime(2026, 7, 1, tzinfo=timezone.utc),
            ai_summary="AI 요약본",
        )
    )

    res = await client.get(
        "/api/stats/calendar/day", params={"date": "2026-07-01"}, headers=auth_headers
    )
    body = res.json()
    assert body[0]["summary_preview"] == "AI 요약본"


async def test_calendar_day_empty_when_no_reviews(client, auth_headers):
    res = await client.get(
        "/api/stats/calendar/day", params={"date": "2026-07-01"}, headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json() == []
