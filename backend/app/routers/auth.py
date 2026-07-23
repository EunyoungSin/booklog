import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import EmailStr

from app.core.config import get_settings
from app.core.deps import get_current_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_verification_code,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import (
    ConfirmVerificationCodeRequest,
    EmailAvailabilityResponse,
    RefreshRequest,
    SendVerificationCodeRequest,
    TokenPair,
    UserCreate,
    UserLogin,
    UserPublic,
)
from app.services.email import send_verification_code_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _issue_token_pair(db: AsyncIOMotorDatabase, user_id: ObjectId) -> TokenPair:
    access_token = create_access_token(str(user_id))
    raw_refresh_token, expires_at = create_refresh_token(str(user_id))

    await db.refresh_tokens.insert_one(
        {
            "user_id": user_id,
            "token_hash": hash_token(raw_refresh_token),
            "expires_at": expires_at,
            "revoked": False,
            "created_at": datetime.now(timezone.utc),
        }
    )

    return TokenPair(access_token=access_token, refresh_token=raw_refresh_token)


@router.get("/check-email", response_model=EmailAvailabilityResponse)
async def check_email(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    email: EmailStr,
):
    existing = await db.users.find_one({"email": email})
    return EmailAvailabilityResponse(available=existing is None)


@router.post("/send-verification-code", status_code=status.HTTP_204_NO_CONTENT)
async def send_verification_code(
    payload: SendVerificationCodeRequest, db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]
):
    existing_user = await db.users.find_one({"email": payload.email})
    if existing_user is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    code, expires_at = create_verification_code()
    await db.email_verification_codes.update_one(
        {"email": payload.email},
        {
            "$set": {
                "code_hash": hash_token(code),
                "expires_at": expires_at,
                "attempts": 0,
                "verified": False,
                "created_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )

    try:
        await send_verification_code_email(payload.email, code)
    except Exception as exc:  # best-effort: the caller can always retry
        logger.warning("Failed to send verification code to %s: %s", payload.email, exc)

    return None


@router.post("/confirm-verification-code", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_verification_code(
    payload: ConfirmVerificationCodeRequest, db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]
):
    settings = get_settings()
    record = await db.email_verification_codes.find_one({"email": payload.email})

    if record is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "인증코드를 먼저 요청해주세요.")
    if record["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "인증코드가 만료되었습니다. 다시 요청해주세요.")
    if record["attempts"] >= settings.email_verification_max_attempts:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "시도 횟수를 초과했습니다. 인증코드를 다시 요청해주세요."
        )

    if hash_token(payload.code) != record["code_hash"]:
        await db.email_verification_codes.update_one(
            {"_id": record["_id"]}, {"$inc": {"attempts": 1}}
        )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "인증코드가 올바르지 않습니다.")

    completion_deadline = datetime.now(timezone.utc) + timedelta(
        minutes=settings.email_verification_completion_window_minutes
    )
    await db.email_verification_codes.update_one(
        {"_id": record["_id"]},
        {"$set": {"verified": True, "expires_at": completion_deadline}},
    )
    return None


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]):
    existing = await db.users.find_one({"email": payload.email})
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    verification = await db.email_verification_codes.find_one({"email": payload.email})
    if (
        verification is None
        or not verification.get("verified", False)
        or verification["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "이메일 인증을 먼저 완료해주세요.")

    user_doc = {
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "name": payload.name,
        "email_verified": True,
        "email_verified_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    await db.email_verification_codes.delete_one({"_id": verification["_id"]})

    return await _issue_token_pair(db, result.inserted_id)


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]):
    user = await db.users.find_one({"email": payload.email})
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    return await _issue_token_pair(db, user["_id"])


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]):
    token_hash = hash_token(payload.refresh_token)
    token_doc = await db.refresh_tokens.find_one({"token_hash": token_hash})

    if (
        token_doc is None
        or token_doc["revoked"]
        or token_doc["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    # rotate: revoke the used refresh token and issue a new pair
    await db.refresh_tokens.update_one({"_id": token_doc["_id"]}, {"$set": {"revoked": True}})

    return await _issue_token_pair(db, token_doc["user_id"])


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]):
    token_hash = hash_token(payload.refresh_token)
    await db.refresh_tokens.update_one({"token_hash": token_hash}, {"$set": {"revoked": True}})
    return None


@router.get("/me", response_model=UserPublic)
async def me(current_user: Annotated[dict, Depends(get_current_user)]):
    return current_user
