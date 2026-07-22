async def _register_book(client, headers, title, isbn, author="한강"):
    res = await client.post(
        "/api/books",
        json={"title": title, "author": author, "isbn": isbn},
        headers=headers,
    )
    return res.json()["id"]


async def _create_review(client, headers, book_id, content, **overrides):
    payload = {
        "book_id": book_id,
        "content": content,
        "rating": 4,
        "tags": ["일반"],
        "visibility": "public",
    }
    payload.update(overrides)
    return await client.post("/api/reviews", json=payload, headers=headers)


async def _create_quote(client, headers, book_id, text, **overrides):
    payload = {"book_id": book_id, "text": text, "tags": ["일반"]}
    payload.update(overrides)
    return await client.post("/api/quotes", json=payload, headers=headers)


async def test_search_books_by_title(client, auth_headers):
    await _register_book(client, auth_headers, "채식주의자", "9788936434120")
    await _register_book(client, auth_headers, "소년이 온다", "9788936434137")

    res = await client.get("/api/search", params={"q": "채식", "type": "books"}, headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "book"
    assert body["items"][0]["title"] == "채식주의자"


async def test_search_reviews_excludes_others_private(
    client, auth_headers, other_auth_headers, book_id
):
    await _create_review(client, auth_headers, book_id, "정말 감동적인 결말이었다")
    await _create_review(
        client, auth_headers, book_id, "감동적이지만 비공개로 남길게요", visibility="private"
    )

    res = await client.get(
        "/api/search", params={"q": "감동", "type": "reviews"}, headers=other_auth_headers
    )
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["snippet"].startswith("정말 감동적인")


async def test_search_reviews_by_tag(client, auth_headers, book_id):
    await _create_review(client, auth_headers, book_id, "내용1", tags=["인생책"])
    await _create_review(client, auth_headers, book_id, "내용2", tags=["별로"])

    res = await client.get(
        "/api/search", params={"q": "인생책", "type": "reviews"}, headers=auth_headers
    )
    assert res.json()["total"] == 1


async def test_search_quotes_only_returns_own(client, auth_headers, other_auth_headers, book_id):
    await _create_quote(client, auth_headers, book_id, "삶은 이상하고도 아름다워요")

    res_owner = await client.get(
        "/api/search", params={"q": "아름다워", "type": "quotes"}, headers=auth_headers
    )
    assert res_owner.json()["total"] == 1

    res_other = await client.get(
        "/api/search", params={"q": "아름다워", "type": "quotes"}, headers=other_auth_headers
    )
    assert res_other.json()["total"] == 0


async def test_search_works_without_auth(client, auth_headers, other_auth_headers, book_id):
    await _register_book(client, auth_headers, "채식주의자", "9788936434120")
    await _create_review(client, auth_headers, book_id, "정말 감동적인 결말이었다")
    await _create_review(
        client, auth_headers, book_id, "감동적이지만 비공개", visibility="private"
    )
    await _create_quote(client, auth_headers, book_id, "아름다운 문장")

    res_books = await client.get("/api/search", params={"q": "채식", "type": "books"})
    assert res_books.status_code == 200
    assert res_books.json()["total"] == 1

    res_reviews = await client.get("/api/search", params={"q": "감동", "type": "reviews"})
    assert res_reviews.status_code == 200
    assert res_reviews.json()["total"] == 1  # only the public one

    res_quotes = await client.get("/api/search", params={"q": "아름다운", "type": "quotes"})
    assert res_quotes.status_code == 200
    assert res_quotes.json()["total"] == 0  # quotes are never public


async def test_search_all_merges_categories(client, auth_headers, book_id):
    await _create_review(client, auth_headers, book_id, "한강 작가의 문체가 좋다")
    await _create_quote(client, auth_headers, book_id, "한강 작품 속 인상적인 문장")

    res = await client.get("/api/search", params={"q": "한강"}, headers=auth_headers)
    body = res.json()
    types = {item["type"] for item in body["items"]}
    assert "book" in types  # author "한강" matches book search
    assert "review" in types
    assert "quote" in types
