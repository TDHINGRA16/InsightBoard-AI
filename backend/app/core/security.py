"""
Security utilities for JWT verification using Supabase JWT secret.
"""

from datetime import datetime, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config import settings
from app.core.exceptions import AuthenticationError


def verify_supabase_token(token: str) -> dict:
    """
    Verify a Supabase JWT token and extract claims.

    Args:
        token: JWT token string from Authorization header

    Returns:
        dict: Decoded token payload containing user info

    Raises:
        AuthenticationError: If token is invalid, expired, or malformed
    """
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience="authenticated",
        )

        # Validate expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(
            tz=timezone.utc
        ):
            raise AuthenticationError("Token has expired")

        # Ensure we have a subject (user ID)
        if not payload.get("sub"):
            raise AuthenticationError("Token missing user identifier")

        return payload

    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def extract_user_from_token(payload: dict) -> dict:
    """
    Extract user information from decoded JWT payload.

    Args:
        payload: Decoded JWT token payload

    Returns:
        dict: User information including id, email, and metadata
    """
    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated"),
        "app_metadata": payload.get("app_metadata", {}),
        "user_metadata": payload.get("user_metadata", {}),
    }
