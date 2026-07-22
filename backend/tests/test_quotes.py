async def _create_quote(client, headers, book_id, **overrides):
    payload = {
        "book_id": book_id,
        "text": "고통과 슬픔이 있는 곳에 사랑이 있어요.",
        "page": 42,
        "tags": ["명언"],
    }
    payload.update(overrides)
    return await client.post("/api/quotes", json=payload, headers=headers)


async def test_create_quote(client, auth_headers, book_id):
    res = await _create_quote(client, auth_headers, book_id)
    assert res.status_code == 201
    body = res.json()
    assert body["page"] == 42
    assert body["tags"] == ["명언"]


async def test_create_quote_unknown_book_404(client, auth_headers):
    res = await _create_quote(client, auth_headers, "000000000000000000000000")
    assert res.status_code == 404


async def test_create_quote_requires_at_least_one_tag(client, auth_headers, book_id):
    res = await _create_quote(client, auth_headers, book_id, tags=[])
    assert res.status_code == 422


async def test_quote_only_visible_to_owner(client, auth_headers, other_auth_headers, book_id):
    created = await _create_quote(client, auth_headers, book_id)
    quote_id = created.json()["id"]

    res_owner = await client.get(f"/api/quotes/{quote_id}", headers=auth_headers)
    assert res_owner.status_code == 200

    res_other = await client.get(f"/api/quotes/{quote_id}", headers=other_auth_headers)
    assert res_other.status_code == 404

    list_res = await client.get(
        "/api/quotes", params={"book_id": book_id}, headers=other_auth_headers
    )
    assert list_res.json()["total"] == 0


async def test_update_quote(client, auth_headers, book_id):
    created = await _create_quote(client, auth_headers, book_id)
    quote_id = created.json()["id"]

    res = await client.put(
        f"/api/quotes/{quote_id}", json={"page": 100}, headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["page"] == 100


async def test_delete_quote(client, auth_headers, book_id):
    created = await _create_quote(client, auth_headers, book_id)
    quote_id = created.json()["id"]

    res = await client.delete(f"/api/quotes/{quote_id}", headers=auth_headers)
    assert res.status_code == 204

    res2 = await client.get(f"/api/quotes/{quote_id}", headers=auth_headers)
    assert res2.status_code == 404
