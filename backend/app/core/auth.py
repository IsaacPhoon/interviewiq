from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi_clerk_auth import (
    ClerkConfig,
    ClerkHTTPBearer,
    HTTPAuthorizationCredentials,
)
from sqlmodel import select

from app.core.config import settings
from app.core.database import SessionDep
from app.models.user import User

clerk_config = ClerkConfig(jwks_url=settings.CLERK_JWKS_URL)

clerk_auth_guard = ClerkHTTPBearer(config=clerk_config, auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(clerk_auth_guard)
    ],
    session: SessionDep,
) -> User:
    """
    Validate Clerk JWT token and return the current user from the database.
    Raise HTTPException with 401 if token is missing/invalid,
    or 403 if user is not found.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing or invalid authorization token.',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    if credentials.decoded is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing or invalid authorization token.',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    clerk_id = credentials.decoded['sub']
    result = await session.exec(select(User).where(User.clerk_id == clerk_id))
    user = result.one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='User not found in database.',
        )

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
