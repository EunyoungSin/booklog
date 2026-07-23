import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


def _send_smtp_email(settings: Settings, to_email: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


async def send_verification_code_email(to_email: str, code: str) -> None:
    settings = get_settings()
    subject = "[BookLog] 이메일 인증코드"
    body = (
        "BookLog 회원가입을 위한 인증코드입니다.\n\n"
        f"인증코드: {code}\n\n"
        f"이 코드는 발급 후 {settings.email_verification_code_expire_minutes}분 동안 유효합니다."
    )

    if not settings.smtp_host:
        logger.warning("SMTP가 설정되어 있지 않아 인증 메일을 실제로 보내지 않았습니다. %s의 인증코드: %s", to_email, code)
        return

    await asyncio.to_thread(_send_smtp_email, settings, to_email, subject, body)
