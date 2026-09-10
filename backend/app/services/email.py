import logging

import httpx

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_RESEND_API_URL = "https://api.resend.com/emails"


class EmailSendError(Exception):
    pass


async def _send_via_resend(settings: Settings, to_email: str, subject: str, body: str) -> None:
    async with httpx.AsyncClient(timeout=10.0) as http_client:
        response = await http_client.post(
            _RESEND_API_URL,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.resend_from_email,
                "to": [to_email],
                "subject": subject,
                "text": body,
            },
        )
    if response.is_error:
        raise EmailSendError(f"Resend API request failed ({response.status_code}): {response.text}")


async def send_verification_code_email(to_email: str, code: str) -> None:
    settings = get_settings()
    subject = "[BookLog] 이메일 인증코드"
    body = (
        "BookLog 회원가입을 위한 인증코드입니다.\n\n"
        f"인증코드: {code}\n\n"
        f"이 코드는 발급 후 {settings.email_verification_code_expire_minutes}분 동안 유효합니다."
    )

    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY가 설정되어 있지 않아 인증 메일을 실제로 보내지 않았습니다. %s의 인증코드: %s", to_email, code)
        return

    await _send_via_resend(settings, to_email, subject, body)
