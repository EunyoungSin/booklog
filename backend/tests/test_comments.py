async def test_create_and_list_comments(client, auth_headers, other_auth_headers, book_id):
    res1 = await client.post(
        f"/api/books/{book_id}/comments", json={"content": "저도 이 책 좋아해요!"}, headers=auth_headers
    )
    assert res1.status_code == 201
    assert res1.json()["author_name"] == "독자"

    res2 = await client.post(
        f"/api/books/{book_id}/comments", json={"content": "결말이 인상적이었어요."}, headers=other_auth_headers
    )
    assert res2.status_code == 201

    list_res = await client.get(f"/api/books/{book_id}/comments", headers=auth_headers)
    body = list_res.json()
    assert body["total"] == 2
    # oldest-first thread order
    assert body["items"][0]["content"] == "저도 이 책 좋아해요!"
    assert body["items"][1]["author_name"] == "다른독자"


async def test_list_comments_works_without_auth(client, auth_headers, book_id):
    await client.post(
        f"/api/books/{book_id}/comments", json={"content": "댓글"}, headers=auth_headers
    )

    res = await client.get(f"/api/books/{book_id}/comments")
    assert res.status_code == 200
    assert res.json()["total"] == 1


async def test_create_comment_unknown_book_404(client, auth_headers):
    res = await client.post(
        "/api/books/000000000000000000000000/comments",
        json={"content": "hi"},
        headers=auth_headers,
    )
    assert res.status_code == 404


async def test_delete_comment_by_non_author_forbidden(
    client, auth_headers, other_auth_headers, book_id
):
    created = await client.post(
        f"/api/books/{book_id}/comments", json={"content": "댓글"}, headers=auth_headers
    )
    comment_id = created.json()["id"]

    res = await client.delete(f"/api/comments/{comment_id}", headers=other_auth_headers)
    assert res.status_code == 403


async def test_delete_comment_by_author(client, auth_headers, book_id):
    created = await client.post(
        f"/api/books/{book_id}/comments", json={"content": "댓글"}, headers=auth_headers
    )
    comment_id = created.json()["id"]

    res = await client.delete(f"/api/comments/{comment_id}", headers=auth_headers)
    assert res.status_code == 204

    list_res = await client.get(f"/api/books/{book_id}/comments", headers=auth_headers)
    assert list_res.json()["total"] == 0
