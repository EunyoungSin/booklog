import app.routers.reviews as reviews_module
from app.services.gemini import AIReviewOutput, GeminiAPIError


async def _create_review_payload(book_id, **overrides):
    payload = {
        "book_id": book_id,
        "content": "좋은 책이었다",
        "rating": 5,
        "tags": ["감상"],
        "visibility": "public",
    }
    payload.update(overrides)
    return payload


async def test_review_creation_calls_ai_once_and_stores_result(
    client, auth_headers, book_id, monkeypatch
):
    calls = []

    async def fake_generate(content, rating):
        calls.append((content, rating))
        return AIReviewOutput(summary="요약입니다", feedback="피드백입니다")

    monkeypatch.setattr(reviews_module, "generate_review_ai_output", fake_generate)

    res = await client.post(
        "/api/reviews", json=await _create_review_payload(book_id), headers=auth_headers
    )
    assert res.status_code == 201
    body = res.json()
    assert body["ai_summary"] == "요약입니다"
    assert body["ai_feedback"] == "피드백입니다"
    assert body["ai_generated_at"] is not None
    assert len(calls) == 1
    assert calls[0] == ("좋은 책이었다", 5)


async def test_review_creation_succeeds_even_if_ai_call_fails(
    client, auth_headers, book_id, monkeypatch
):
    async def failing_generate(content, rating):
        raise GeminiAPIError("boom")

    monkeypatch.setattr(reviews_module, "generate_review_ai_output", failing_generate)

    res = await client.post(
        "/api/reviews", json=await _create_review_payload(book_id), headers=auth_headers
    )
    assert res.status_code == 201
    body = res.json()
    assert body["ai_summary"] is None
    assert body["ai_feedback"] is None


async def test_ai_regenerate_is_explicit_and_overwrites_summary(
    client, auth_headers, book_id, monkeypatch
):
    calls = []

    async def fake_generate(content, rating):
        calls.append(1)
        return AIReviewOutput(summary=f"요약 {len(calls)}", feedback=f"피드백 {len(calls)}")

    monkeypatch.setattr(reviews_module, "generate_review_ai_output", fake_generate)

    created = await client.post(
        "/api/reviews", json=await _create_review_payload(book_id), headers=auth_headers
    )
    review_id = created.json()["id"]
    assert len(calls) == 1  # 생성 시 자동 1회 호출
    assert created.json()["ai_summary"] == "요약 1"

    res = await client.post(f"/api/reviews/{review_id}/ai-regenerate", headers=auth_headers)
    assert res.status_code == 200
    assert len(calls) == 2  # 명시적 재생성 요청 시에만 추가 호출
    assert res.json()["ai_summary"] == "요약 2"


async def test_ai_regenerate_forbidden_for_non_owner(
    client, auth_headers, other_auth_headers, book_id, monkeypatch
):
    async def fake_generate(content, rating):
        return AIReviewOutput(summary="s", feedback="f")

    monkeypatch.setattr(reviews_module, "generate_review_ai_output", fake_generate)

    created = await client.post(
        "/api/reviews", json=await _create_review_payload(book_id), headers=auth_headers
    )
    review_id = created.json()["id"]

    res = await client.post(
        f"/api/reviews/{review_id}/ai-regenerate", headers=other_auth_headers
    )
    assert res.status_code == 403


async def test_ai_regenerate_propagates_gateway_error(
    client, auth_headers, book_id, monkeypatch
):
    async def fake_generate_ok(content, rating):
        return AIReviewOutput(summary="s", feedback="f")

    monkeypatch.setattr(reviews_module, "generate_review_ai_output", fake_generate_ok)
    created = await client.post(
        "/api/reviews", json=await _create_review_payload(book_id), headers=auth_headers
    )
    review_id = created.json()["id"]

    async def failing_generate(content, rating):
        raise GeminiAPIError("quota exceeded")

    monkeypatch.setattr(reviews_module, "generate_review_ai_output", failing_generate)

    res = await client.post(f"/api/reviews/{review_id}/ai-regenerate", headers=auth_headers)
    assert res.status_code == 502
