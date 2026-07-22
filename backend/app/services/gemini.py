from google import genai
from google.genai import types
from pydantic import BaseModel

from app.core.config import get_settings

_PROMPT_TEMPLATE = """당신은 독서 기록 앱 BookLog의 AI 어시스턴트입니다.
아래는 한 사용자가 작성한 독후감입니다 (별점 {rating}/5).

---
{content}
---

이 독후감을 바탕으로 다음 두 가지를 한국어로 작성하세요.
1. summary: 독후감 내용을 2~3문장으로 요약합니다.
2. feedback: 글쓰기 관점에서 건설적이고 구체적인 피드백을 2~3문장으로 제공합니다
   (문장 구조, 구체성, 감상의 깊이 등을 언급하세요).
"""


class GeminiAPIError(Exception):
    pass


class AIReviewOutput(BaseModel):
    summary: str
    feedback: str


async def generate_review_ai_output(content: str, rating: int) -> AIReviewOutput:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiAPIError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = _PROMPT_TEMPLATE.format(rating=rating, content=content)

    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AIReviewOutput,
            ),
        )
    except Exception as exc:
        raise GeminiAPIError(f"Gemini API 호출 실패: {exc}") from exc

    if response.parsed is not None:
        return response.parsed

    try:
        return AIReviewOutput.model_validate_json(response.text)
    except Exception as exc:
        raise GeminiAPIError("Gemini 응답을 파싱할 수 없습니다") from exc
