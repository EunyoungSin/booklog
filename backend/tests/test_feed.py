async def _create_review(client, headers, book_id, **overrides):
    payload = {
        "book_id": book_id,
        "content": "리뷰 내용",
        "rating": 4,
        "tags": ["일반"],
        "visibility": "public",
    }
    payload.update(overrides)
    return await client.post("/api/reviews", json=payload, headers=headers)


async def test_feed_shows_only_public_reviews_latest_first(
    client, auth_headers, other_auth_headers, book_id
):
    await _create_review(client, auth_headers, book_id, content="첫번째 공개 리뷰")
    await _create_review(client, auth_headers, book_id, content="비공개 리뷰", visibility="private")
    await _create_review(client, other_auth_headers, book_id, content="두번째 공개 리뷰")

    res = await client.get("/api/feed", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    # latest first
    assert body["items"][0]["content"] == "두번째 공개 리뷰"
    assert body["items"][0]["author_name"] == "다른독자"
    assert body["items"][0]["book"]["title"] == "채식주의자"
    assert body["items"][1]["content"] == "첫번째 공개 리뷰"


async def test_feed_accessible_without_authentication(client, auth_headers, book_id):
    await _create_review(client, auth_headers, book_id, content="공개 리뷰")
    await _create_review(client, auth_headers, book_id, content="비공개 리뷰", visibility="private")

    res = await client.get("/api/feed")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["content"] == "공개 리뷰"
    assert body["items"][0]["liked_by_me"] is False


async def test_feed_tag_filter(client, auth_headers, book_id):
    await _create_review(client, auth_headers, book_id, content="a", tags=["감동"])
    await _create_review(client, auth_headers, book_id, content="b", tags=["지루함"])

    res = await client.get("/api/feed", params={"tag": "감동"}, headers=auth_headers)
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["content"] == "a"


async def test_book_public_reviews_endpoint_hides_private_and_shows_author(
    client, auth_headers, other_auth_headers, book_id
):
    await _create_review(client, auth_headers, book_id, content="공개")
    await _create_review(client, auth_headers, book_id, content="비공개", visibility="private")

    res = await client.get(f"/api/books/{book_id}/reviews", headers=other_auth_headers)
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["content"] == "공개"
    assert body["items"][0]["author_name"] == "독자"
    assert body["items"][0]["like_count"] == 0
    assert body["items"][0]["liked_by_me"] is False


async def test_book_public_reviews_reflects_like_state(client, auth_headers, other_auth_headers, book_id):
    created = await _create_review(client, auth_headers, book_id, content="공개")
    review_id = created.json()["id"]
    await client.post(f"/api/reviews/{review_id}/like", headers=other_auth_headers)

    res = await client.get(f"/api/books/{book_id}/reviews", headers=other_auth_headers)
    item = res.json()["items"][0]
    assert item["like_count"] == 1
    assert item["liked_by_me"] is True
