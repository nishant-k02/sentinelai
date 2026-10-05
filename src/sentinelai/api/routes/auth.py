from __future__ import annotations

import uuid

from fastapi import APIRouter, Request, Response, status

from sentinelai.api.auth import AdminDep, ViewerDep
from sentinelai.api.deps import (
    OrganizationRepositoryDep,
    RedisDep,
    RefreshTokenRepositoryDep,
    SessionDep,
    SettingsDep,
    UserRepositoryDep,
    enforce_login_rate_limit,
)
from sentinelai.modules.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserRead,
)
from sentinelai.modules.auth.use_cases import (
    TokenPair,
    TokenReuseDetectedError,
    authenticate_user,
    refresh_access_token,
    register_user,
    revoke_refresh_token,
)
from sentinelai.platform.errors import AuthenticationError, NotFoundError

router = APIRouter(prefix="/v1", tags=["auth"])


def _token_response(pair: TokenPair) -> TokenResponse:
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    settings: SettingsDep,
    redis: RedisDep,
    user_repo: UserRepositoryDep,
    token_repo: RefreshTokenRepositoryDep,
) -> TokenResponse:
    # request.client.host is the TCP peer. Behind a reverse proxy / ingress
    # that is the proxy, not the user; running behind one means configuring
    # trusted forwarded headers (uvicorn --proxy-headers). Deployment
    # concern, recorded in SECURITY.md.
    ip = request.client.host if request.client else "unknown"
    await enforce_login_rate_limit(redis, ip, body.email)

    pair = await authenticate_user(
        settings, user_repo, token_repo, email=body.email, password=body.password
    )
    return _token_response(pair)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    session: SessionDep,
    settings: SettingsDep,
    user_repo: UserRepositoryDep,
    token_repo: RefreshTokenRepositoryDep,
) -> TokenResponse:
    try:
        pair = await refresh_access_token(
            settings, user_repo, token_repo, refresh_token=body.refresh_token
        )
    except TokenReuseDetectedError as exc:
        # The use case just revoked every session for this user. Raising an
        # exception makes get_session ROLL BACK the request's transaction,
        # which would silently undo that revocation, so persist it first.
        # `session` is the same instance the repositories hold: FastAPI
        # caches a dependency per request.
        await session.commit()
        raise AuthenticationError("invalid refresh token") from exc
    return _token_response(pair)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def logout(body: LogoutRequest, token_repo: RefreshTokenRepositoryDep) -> Response:
    await revoke_refresh_token(token_repo, refresh_token=body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserRead)
async def me(current: ViewerDep, user_repo: UserRepositoryDep) -> UserRead:
    user = await user_repo.get(current.id)
    if user is None:
        # A valid access token can outlive the account it was issued to.
        raise AuthenticationError("invalid or expired token")
    return UserRead.model_validate(user)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    response: Response,
    admin: AdminDep,
    org_repo: OrganizationRepositoryDep,
    user_repo: UserRepositoryDep,
) -> UserRead:
    # organization_id comes from the admin's token, never from the body:
    # an admin can only create users in their own organization.
    user = await register_user(
        org_repo,
        user_repo,
        organization_id=admin.organization_id,
        email=body.email,
        password=body.password,
        role=body.role,
    )
    response.headers["Location"] = f"/v1/users/{user.id}"
    return UserRead.model_validate(user)


@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(user_id: uuid.UUID, admin: AdminDep, user_repo: UserRepositoryDep) -> UserRead:
    user = await user_repo.get(user_id)
    # Another organization's user is reported as "not found", not
    # "forbidden": a 403 would confirm that the id exists in someone else's
    # tenant, which is itself a leak.
    if user is None or user.organization_id != admin.organization_id:
        raise NotFoundError(f"user {user_id} not found")
    return UserRead.model_validate(user)
