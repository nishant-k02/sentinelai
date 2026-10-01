from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from sentinelai.platform.db import Base


class Role(StrEnum):
    VIEWER = "viewer"
    RESPONDER = "responder"
    ADMIN = "admin"

    @property
    def rank(self) -> int:
        """Ordering for RBAC checks: ADMIN implies RESPONDER implies VIEWER.
        A plain StrEnum has no inherent order; this gives require_role
        (Auth-5) one place to ask 'is this role at least as privileged as
        that one' instead of scattering role comparisons through the
        codebase. APPROVER is deliberately absent — it governs remediation
        approval (M8), nothing that exists yet."""
        return {Role.VIEWER: 0, Role.RESPONDER: 1, Role.ADMIN: 2}[self]


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    # 320 = RFC 5321's max email length (64 local-part + '@' + 255 domain).
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SQLEnum(Role, name="user_role"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 64 = length of a SHA-256 hex digest, exactly.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
