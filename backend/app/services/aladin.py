import httpx

from app.core.config import get_settings
from app.models.book import BookSearchResult

_SEARCH_PATH = "/ItemSearch.aspx"


class AladinAPIError(Exception):
    pass


async def search_books(query: str, max_results: int = 20) -> list[BookSearchResult]:
    settings = get_settings()
    if not settings.aladin_ttb_key:
        raise AladinAPIError("ALADIN_TTB_KEY is not configured")

    params = {
        "ttbkey": settings.aladin_ttb_key,
        "Query": query,
        "QueryType": "Keyword",
        "MaxResults": max(1, min(max_results, 50)),
        "start": 1,
        "SearchTarget": "Book",
        "output": "js",
        "Version": "20131101",
        "Cover": "Big",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http_client:
            response = await http_client.get(
                f"{settings.aladin_api_base_url}{_SEARCH_PATH}", params=params
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise AladinAPIError(f"Failed to reach Aladin API: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise AladinAPIError("Aladin API returned a non-JSON response") from exc

    if "errorCode" in data:
        raise AladinAPIError(data.get("errorMessage", "Unknown Aladin API error"))

    return [_to_search_result(item) for item in data.get("item", [])]


def _to_search_result(item: dict) -> BookSearchResult:
    return BookSearchResult(
        title=(item.get("title") or "").strip(),
        author=item.get("author"),
        isbn=item.get("isbn13") or item.get("isbn"),
        cover_url=item.get("cover"),
        publisher=item.get("publisher"),
        description=item.get("description"),
        pub_date=item.get("pubDate"),
    )
