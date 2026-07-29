import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.db.mongodb import get_db
from app.main import app
from app.services.gemini import GeminiAPIError


@pytest_asyncio.fixture(autouse=True)
def _no_real_gemini_calls(monkeypatch):
    """개발자의 .env에 설정된 GEMINI_API_KEY와 무관하게, 테스트는 절대 실제
    Gemini API를 호출해서는 안 된다. 개별 테스트(예: tests/test_ai.py)는
    특정 성공/실패 시나리오를 검증하기 위해 각자의 monkeypatch로 이 설정을
    테스트별로 오버라이드한다.
    """

    async def _unavailable(content: str, rating: int):
        raise GeminiAPIError("Gemini calls are disabled in the test suite")

    monkeypatch.setattr("app.routers.reviews.generate_review_ai_output", _unavailable)


@pytest_asyncio.fixture(autouse=True)
def sent_verification_codes(monkeypatch):
    """개발자의 .env에 무엇이 설정되어 있든, 테스트는 절대 실제 SMTP 서버를
    호출해서는 안 된다. 대신 (to_email, code) 쌍을 저장해두어 테스트(및 아래의
    _register_and_get_headers 헬퍼)가 실제 받은편지함 없이 회원가입 플로우를
    진행할 수 있게 한다.
    """
    sent: list[tuple[str, str]] = []

    async def _fake_send(to_email: str, code: str) -> None:
        sent.append((to_email, code))

    monkeypatch.setattr("app.routers.auth.send_verification_code_email", _fake_send)
    return sent


@pytest_asyncio.fixture
async def db():
    mock_client = AsyncMongoMockClient()
    database = mock_client["booklog_test"]
    yield database


@pytest_asyncio.fixture
async def client(db):
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _register_and_get_headers(
    client, sent_verification_codes: list[tuple[str, str]], email: str, name: str
) -> dict:
    await client.post("/api/auth/send-verification-code", json={"email": email})
    code = sent_verification_codes[-1][1]
    await client.post("/api/auth/confirm-verification-code", json={"email": email, "code": code})

    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "name": name},
    )
    access_token = res.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def auth_headers(client, sent_verification_codes):
    return await _register_and_get_headers(client, sent_verification_codes, "reader@example.com", "독자")


@pytest_asyncio.fixture
async def other_auth_headers(client, sent_verification_codes):
    return await _register_and_get_headers(
        client, sent_verification_codes, "other@example.com", "다른독자"
    )


@pytest_asyncio.fixture
async def book_id(client, auth_headers):
    res = await client.post(
        "/api/books",
        json={"title": "채식주의자", "author": "한강", "isbn": "9788936434120"},
        headers=auth_headers,
    )
    return res.json()["id"]
