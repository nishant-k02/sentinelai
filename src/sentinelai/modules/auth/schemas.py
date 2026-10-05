from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from sentinelai.modules.auth.models import Role
from sentinelai.modules.auth.policy import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH


class LoginRequest(BaseModel):
    # Plain str, not EmailStr: login should never reveal *why* something was
    # rejected, and a format error is just another signal. Bounded so a
    # megabyte-long "email" can't be pushed through the stack.
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=512)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=512)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    # No organization_id: it comes from the calling admin's token, never
    # from the request body. This is the whole point of the milestone.
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    role: Role


class UserRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    role: Role
    created_at: datetime

    model_config = {"from_attributes": True}
