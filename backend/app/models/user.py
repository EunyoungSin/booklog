from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.common import PyObjectId


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(validation_alias="_id")
    email: EmailStr
    name: str
    email_verified: bool = True
    created_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmailAvailabilityResponse(BaseModel):
    available: bool


class SendVerificationCodeRequest(BaseModel):
    email: EmailStr


class ConfirmVerificationCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
