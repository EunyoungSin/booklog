async def _create_review(client, headers, book_id, **overrides):
    payload = {
        "book_id": book_id,
        "content": "정말 인상 깊게 읽었다.",
        "rating": 5,
        "tags": ["소설", " 한강 "],
        "visibility": "public",
    }
    payload.update(overrides)
    return await client.post("/api/reviews", json=payload, headers=headers)


async def test_create_review(client, auth_headers, book_id):
    res = await _create_review(client, auth_headers, book_id)
    assert res.status_code == 201
    body = res.json()
    assert body["rating"] == 5
    assert body["tags"] == ["소설", "한강"]  # trimmed, order preserved, no dupes
    assert body["visibility"] == "public"
    assert body["ai_summary"] is None


async def test_create_review_invalid_rating_rejected(client, auth_headers, book_id):
    res = await _create_review(client, auth_headers, book_id, rating=6)
    assert res.status_code == 422


async def test_create_review_unknown_book_404(client, auth_headers):
    res = await _create_review(client, auth_headers, "000000000000000000000000")
    assert res.status_code == 404


async def test_create_review_requires_at_least_one_tag(client, auth_headers, book_id):
    res = await _create_review(client, auth_headers, book_id, tags=[])
    assert res.status_code == 422


async def test_create_review_rejects_whitespace_only_tags(client, auth_headers, book_id):
    res = await _create_review(client, auth_headers, book_id, tags=["   "])
    assert res.status_code == 422


async def test_update_review_cannot_clear_all_tags(client, auth_headers, book_id):
    created = await _create_review(client, auth_headers, book_id)
    review_id = created.json()["id"]

    res = await client.put(f"/api/reviews/{review_id}", json={"tags": []}, headers=auth_headers)
    assert res.status_code == 422


async def test_private_review_hidden_from_others(client, auth_headers, other_auth_headers, book_id):
    created = await _create_review(client, auth_headers, book_id, visibility="private")
    review_id = created.json()["id"]

    # owner can see it
    res_owner = await client.get(f"/api/reviews/{review_id}", headers=auth_headers)
    assert res_owner.status_code == 200

    # another user cannot
    res_other = await client.get(f"/api/reviews/{review_id}", headers=other_auth_headers)
    assert res_other.status_code == 404


async def test_private_review_excluded_from_default_list(
    client, auth_headers, other_auth_headers, book_id
):
    await _create_review(client, auth_headers, book_id, visibility="private")
    await _create_review(client, auth_headers, book_id, visibility="public", content="공개 리뷰")

    res = await client.get(
        "/api/reviews", params={"book_id": book_id}, headers=other_auth_headers
    )
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["visibility"] == "public"


async def test_mine_filter_returns_own_private_and_public(client, auth_headers, book_id):
    await _create_review(client, auth_headers, book_id, visibility="private")
    await _create_review(client, auth_headers, book_id, visibility="public", content="공개 리뷰")

    res = await client.get("/api/reviews", params={"mine": True}, headers=auth_headers)
    assert res.json()["total"] == 2


async def test_update_review_by_non_owner_forbidden(
    client, auth_headers, other_auth_headers, book_id
):
    created = await _create_review(client, auth_headers, book_id)
    review_id = created.json()["id"]

    res = await client.put(
        f"/api/reviews/{review_id}", json={"rating": 1}, headers=other_auth_headers
    )
    assert res.status_code == 403


async def test_update_review_by_owner(client, auth_headers, book_id):
    created = await _create_review(client, auth_headers, book_id)
    review_id = created.json()["id"]

    res = await client.put(
        f"/api/reviews/{review_id}",
        json={"rating": 3, "visibility": "private"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["rating"] == 3
    assert body["visibility"] == "private"


async def test_delete_review(client, auth_headers, book_id):
    created = await _create_review(client, auth_headers, book_id)
    review_id = created.json()["id"]

    res = await client.delete(f"/api/reviews/{review_id}", headers=auth_headers)
    assert res.status_code == 204

    res2 = await client.get(f"/api/reviews/{review_id}", headers=auth_headers)
    assert res2.status_code == 404


async def test_tag_filter(client, auth_headers, book_id):
    await _create_review(client, auth_headers, book_id, tags=["감동"], content="a")
    await _create_review(client, auth_headers, book_id, tags=["지루함"], content="b")

    res = await client.get("/api/reviews", params={"tag": "감동"}, headers=auth_headers)
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["tags"] == ["감동"]
