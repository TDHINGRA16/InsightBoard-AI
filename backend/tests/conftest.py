"""
Pytest configuration and fixtures.
"""

import os
import pytest
from typing import Generator
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SUPABASE_JWT_SECRET"] = "test-secret-key-for-testing-only"
os.environ["GROQ_API_KEY"] = "test-groq-key"
os.environ["DEBUG"] = "true"

from app.database import Base, get_db
from app.main import app
from app.models.user import Profile


# Test database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a clean database session for each test.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database dependency override.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> Profile:
    """
    Create a test user.
    """
    import uuid

    user = Profile(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def auth_headers(test_user: Profile) -> dict:
    """
    Create mock authentication headers.
    """
    import jwt
    from datetime import datetime, timedelta

    payload = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }

    token = jwt.encode(
        payload,
        os.environ["SUPABASE_JWT_SECRET"],
        algorithm="HS256",
    )

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_redis():
    """
    Mock Redis for tests.
    """
    with patch("app.services.cache_service.redis") as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.ping.return_value = True
        yield mock


@pytest.fixture
def mock_groq():
    """
    Mock Groq LLM for tests.
    """
    with patch("app.services.nlp_service.Groq") as mock:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"tasks": [{"title": "Test Task", "priority": "high"}], "dependencies": []}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock.return_value = mock_client
        yield mock


@pytest.fixture
def sample_transcript_content():
    """
    Sample transcript text for testing.
    """
    return """
    Project Meeting Notes - January 28, 2026

    Discussion Points:
    1. Alice will set up the development environment by Friday.
    2. Bob needs to complete the database schema design before any coding starts.
    3. Carol will write the API documentation after the schema is finalized.
    4. The frontend team needs to wait for API documentation before starting.

    Dependencies:
    - API documentation depends on database schema
    - Frontend development depends on API documentation
    - Testing can only begin after frontend is complete
    """


@pytest.fixture
def sample_llm_response():
    """
    Sample LLM response for testing.
    """
    return {
        "tasks": [
            {
                "title": "Set up development environment",
                "description": "Configure dev tools and environment",
                "assignee": "Alice",
                "priority": "high",
                "deadline": "2026-02-01",
                "estimated_hours": 8,
            },
            {
                "title": "Complete database schema design",
                "description": "Design and document database schema",
                "assignee": "Bob",
                "priority": "critical",
                "deadline": "2026-01-31",
                "estimated_hours": 16,
            },
            {
                "title": "Write API documentation",
                "description": "Document all API endpoints",
                "assignee": "Carol",
                "priority": "high",
                "deadline": "2026-02-05",
                "estimated_hours": 12,
            },
        ],
        "dependencies": [
            {
                "task_title": "Write API documentation",
                "depends_on_title": "Complete database schema design",
            },
        ],
    }
