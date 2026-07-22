async def _create_review(client, headers, book_id, **overrides):
    payload = {
        "book_id": book_id,
        "content": "좋은 책이었다.",
        "rating": 4,
        "tags": ["일반"],
        "visibility": "public",
    }
    payload.update(overrides)
    res = await client.post("/api/reviews", json=payload, headers=headers)
    return res.json()["id"]


async def test_toggle_like_then_unlike(client, auth_headers, other_auth_headers, book_id):
    review_id = await _create_review(client, auth_headers, book_id)

    res1 = await client.post(f"/api/reviews/{review_id}/like", headers=other_auth_headers)
    assert res1.status_code == 200
    assert res1.json() == {"liked": True, "like_count": 1}

    res2 = await client.post(f"/api/reviews/{review_id}/like", headers=other_auth_headers)
    assert res2.json() == {"liked": False, "like_count": 0}


async def test_get_likes_reflects_state(client, auth_headers, other_auth_headers, book_id):
    review_id = await _create_review(client, auth_headers, book_id)
    await client.post(f"/api/reviews/{review_id}/like", headers=other_auth_headers)

    res = await client.get(f"/api/reviews/{review_id}/likes", headers=other_auth_headers)
    assert res.json() == {"liked": True, "like_count": 1}

    res_owner_view = await client.get(f"/api/reviews/{review_id}/likes", headers=auth_headers)
    assert res_owner_view.json() == {"liked": False, "like_count": 1}


async def test_cannot_like_private_review_of_another_user(
    client, auth_headers, other_auth_headers, book_id
):
    review_id = await _create_review(client, auth_headers, book_id, visibility="private")

    res = await client.post(f"/api/reviews/{review_id}/like", headers=other_auth_headers)
    assert res.status_code == 404
