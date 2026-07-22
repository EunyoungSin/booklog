from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import (
    RefreshRequest,
    TokenPair,
    UserCreate,
    UserLogin,
    UserPublic,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _issue_token_pair(db: AsyncIOMotorDatabase, user_id: ObjectId) -> TokenPair:
    access_token = create_access_token(str(user_id))
    raw_refresh_token, expires_at = create_refresh_token(str(user_id))

    await db.refresh_tokens.insert_one(
        {
            "user_id": user_id,
            "token_hash": hash_refresh_token(raw_refresh_token),
            "expires_at": expires_at,
            "revoked": False,
            "created_at": datetime.now(timezone.utc),
        }
    )

    return TokenPair(access_token=access_token, refresh_token=raw_refresh_token)


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]):
    existing = await db.users.find_one({"email": payload.email})
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user_doc = {
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "name": payload.name,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)

    return await _issue_token_pair(db, result.inserted_id)


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]):
    user = await db.users.find_one({"email": payload.email})
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    return await _issue_token_pair(db, user["_id"])


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]):
    token_hash = hash_refresh_token(payload.refresh_token)
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
    token_hash = hash_refresh_token(payload.refresh_token)
    await db.refresh_tokens.update_one({"token_hash": token_hash}, {"$set": {"revoked": True}})
    return None


@router.get("/me", response_model=UserPublic)
async def me(current_user: Annotated[dict, Depends(get_current_user)]):
    return current_user
