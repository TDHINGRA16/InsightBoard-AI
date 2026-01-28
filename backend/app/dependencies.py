"""
Dependency injection helpers for FastAPI routes.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import CurrentUser

# Type aliases for cleaner route signatures
DbSession = Annotated[Session, Depends(get_db)]
AuthUser = Annotated[CurrentUser, Depends(get_current_user)]
