import respx
from httpx import Response

ALADIN_URL = "https://www.aladin.co.kr/ttb/api/ItemSearch.aspx"


def _aladin_item(title="채식주의자", isbn13="9788936434120"):
    return {
        "title": title,
        "author": "한강 (지은이)",
        "isbn13": isbn13,
        "cover": "https://image.aladin.co.kr/cover.jpg",
        "publisher": "창비",
        "description": "채식주의자 소개",
        "pubDate": "2007-10-30",
    }


@respx.mock
async def test_search_books_proxies_aladin(client, auth_headers):
    respx.get(ALADIN_URL).mock(return_value=Response(200, json={"item": [_aladin_item()]}))

    res = await client.get(
        "/api/books/search", params={"query": "채식주의자"}, headers=auth_headers
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["title"] == "채식주의자"
    assert body[0]["isbn"] == "9788936434120"


@respx.mock
async def test_search_works_without_auth(client):
    respx.get(ALADIN_URL).mock(return_value=Response(200, json={"item": [_aladin_item()]}))

    res = await client.get("/api/books/search", params={"query": "test"})
    assert res.status_code == 200
    assert len(res.json()) == 1


async def _register_book(client, headers, **overrides):
    payload = {
        "title": "채식주의자",
        "author": "한강",
        "isbn": "9788936434120",
        "cover_url": "https://image.aladin.co.kr/cover.jpg",
        "publisher": "창비",
        "description": "설명",
    }
    payload.update(overrides)
    return await client.post("/api/books", json=payload, headers=headers)


async def test_register_book_adds_to_library(client, auth_headers):
    res = await _register_book(client, auth_headers)
    assert res.status_code == 201
    book = res.json()
    assert book["title"] == "채식주의자"

    lib_res = await client.get("/api/library/me", headers=auth_headers)
    assert lib_res.status_code == 200
    lib_body = lib_res.json()
    assert lib_body["total"] == 1
    assert lib_body["items"][0]["book"]["id"] == book["id"]


async def test_register_same_isbn_twice_does_not_duplicate_book(client, auth_headers):
    first = await _register_book(client, auth_headers)
    second = await _register_book(client, auth_headers)
    assert first.json()["id"] == second.json()["id"]

    lib_res = await client.get("/api/library/me", headers=auth_headers)
    assert lib_res.json()["total"] == 1


async def test_get_book_detail(client, auth_headers):
    created = await _register_book(client, auth_headers)
    book_id = created.json()["id"]

    res = await client.get(f"/api/books/{book_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["isbn"] == "9788936434120"


async def test_get_book_detail_not_found(client, auth_headers):
    res = await client.get("/api/books/000000000000000000000000", headers=auth_headers)
    assert res.status_code == 404


async def test_get_book_detail_works_without_auth(client, auth_headers):
    created = await _register_book(client, auth_headers)
    book_id = created.json()["id"]

    res = await client.get(f"/api/books/{book_id}")
    assert res.status_code == 200
    assert res.json()["isbn"] == "9788936434120"


async def test_book_public_reviews_work_without_auth(client, auth_headers):
    created = await _register_book(client, auth_headers)
    book_id = created.json()["id"]
    await client.post(
        "/api/reviews",
        json={
            "book_id": book_id,
            "content": "공개 리뷰",
            "rating": 5,
            "tags": ["일반"],
            "visibility": "public",
        },
        headers=auth_headers,
    )

    res = await client.get(f"/api/books/{book_id}/reviews")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["liked_by_me"] is False


async def test_remove_from_library(client, auth_headers):
    created = await _register_book(client, auth_headers)
    book_id = created.json()["id"]

    res = await client.delete(f"/api/library/{book_id}", headers=auth_headers)
    assert res.status_code == 204

    lib_res = await client.get("/api/library/me", headers=auth_headers)
    assert lib_res.json()["total"] == 0

    res2 = await client.delete(f"/api/library/{book_id}", headers=auth_headers)
    assert res2.status_code == 404
