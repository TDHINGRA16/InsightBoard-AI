"""
Authentication middleware and dependency for Supabase JWT verification.
"""

from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthenticationError
from app.core.security import extract_user_from_token, verify_supabase_token
from app.database import get_db
from app.models.user import Profile
from app.schemas.common import CurrentUser
from sqlalchemy.orm import Session

# HTTP Bearer token extractor
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """
    Dependency that validates JWT token and returns current user.

    This dependency:
    1. Extracts Bearer token from Authorization header
    2. Verifies token using Supabase JWT secret
    3. Upserts user profile if needed
    4. Returns CurrentUser schema

    Args:
        request: FastAPI request object
        credentials: Bearer token credentials
        db: Database session

    Returns:
        CurrentUser: Authenticated user information

    Raises:
        AuthenticationError: If token is missing, invalid, or expired
    """
    if not credentials:
        raise AuthenticationError("Missing authorization header")

    token = credentials.credentials

    # Verify token and extract payload
    payload = verify_supabase_token(token)
    user_info = extract_user_from_token(payload)

    # Upsert profile on first login
    user_id = user_info["id"]
    email = user_info.get("email")

    profile = db.query(Profile).filter(Profile.id == user_id).first()

    if not profile and email:
        # Create profile for new user
        profile = Profile(
            id=user_id,
            email=email,
            full_name=user_info.get("user_metadata", {}).get("full_name", ""),
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return CurrentUser(
        id=user_id,
        email=email or "",
        full_name=profile.full_name if profile else "",
    )


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[CurrentUser]:
    """
    Optional authentication - returns None if no valid token.

    Useful for endpoints that have different behavior for
    authenticated vs anonymous users.

    Args:
        request: FastAPI request object
        credentials: Optional Bearer token credentials
        db: Database session

    Returns:
        Optional[CurrentUser]: User if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(request, credentials, db)
    except AuthenticationError:
        return None
