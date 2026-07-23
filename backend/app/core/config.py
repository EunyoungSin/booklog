from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "booklog"

    # JWT
    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # CORS
    cors_origins: str = "http://localhost:5173"

    # Email (SMTP) - if smtp_host is blank, verification codes are logged instead of sent
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@booklog.local"

    # email verification code (sent during registration, before the account exists)
    email_verification_code_expire_minutes: int = 10
    # once a code is confirmed, how long the caller has to finish POST /api/auth/register
    email_verification_completion_window_minutes: int = 30
    email_verification_max_attempts: int = 5

    # Aladin (알라딘) API
    aladin_ttb_key: str = ""
    aladin_api_base_url: str = "https://www.aladin.co.kr/ttb/api"

    # Gemini
    gemini_api_key: str = ""
    # "gemini-2.5-flash-lite"는 계정에 따라 신규 사용자에게 404로 막혀 있을 수 있어,
    # 항상 현재 권장 lite 모델을 가리키는 별칭(alias)을 기본값으로 사용한다.
    gemini_model: str = "gemini-flash-lite-latest"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
