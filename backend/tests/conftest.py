import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.db.mongodb import get_db
from app.main import app
from app.services.gemini import GeminiAPIError


@pytest_asyncio.fixture(autouse=True)
def _no_real_gemini_calls(monkeypatch):
    """Tests must never hit the real Gemini API, regardless of what GEMINI_API_KEY is
    set in the developer's .env. Individual tests (e.g. tests/test_ai.py) override this
    per-test with their own monkeypatch to exercise specific success/failure scenarios.
    """

    async def _unavailable(content: str, rating: int):
        raise GeminiAPIError("Gemini calls are disabled in the test suite")

    monkeypatch.setattr("app.routers.reviews.generate_review_ai_output", _unavailable)


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


async def _register_and_get_headers(client, email: str, name: str) -> dict:
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "name": name},
    )
    access_token = res.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def auth_headers(client):
    return await _register_and_get_headers(client, "reader@example.com", "독자")


@pytest_asyncio.fixture
async def other_auth_headers(client):
    return await _register_and_get_headers(client, "other@example.com", "다른독자")


@pytest_asyncio.fixture
async def book_id(client, auth_headers):
    res = await client.post(
        "/api/books",
        json={"title": "채식주의자", "author": "한강", "isbn": "9788936434120"},
        headers=auth_headers,
    )
    return res.json()["id"]
