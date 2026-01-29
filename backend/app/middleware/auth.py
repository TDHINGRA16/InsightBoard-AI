"""
Authentication dependency for FastAPI routes.

Verifies Supabase JWT from `Authorization: Bearer <token>` header and returns a
minimal `CurrentUser` object.
"""

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.core.security import extract_user_from_token, verify_supabase_token
from app.database import get_db
from app.models.user import Profile
from app.schemas.common import CurrentUser


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """
    FastAPI dependency: returns authenticated user (Supabase JWT).

    Also ensures a `profiles` row exists for this user id.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationError("Missing Authorization bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise AuthenticationError("Missing token")

    payload = await verify_supabase_token(token)
    user = extract_user_from_token(payload)

    user_id = user.get("id")
    if not user_id:
        raise AuthenticationError("Invalid token: missing subject")

    # Ensure profile exists (best-effort)
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile:
        profile = Profile(
            id=user_id,
            email=user.get("email") or "",
            full_name=(user.get("user_metadata") or {}).get("full_name") or "",
            avatar_url=(user.get("user_metadata") or {}).get("avatar_url"),
        )
        db.add(profile)
        db.commit()

    return CurrentUser(
        id=str(user_id),
        email=user.get("email"),
        role=user.get("role") or "authenticated",
    )

