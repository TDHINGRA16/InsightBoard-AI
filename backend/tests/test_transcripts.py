"""
Tests for transcript endpoints.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.transcript import Transcript, TranscriptStatus
from app.models.user import Profile


class TestTranscriptEndpoints:
    """Tests for transcript CRUD operations."""

    def test_health_check(self, client: TestClient, mock_redis):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "InsightBoard" in data["name"]

    @patch("app.middleware.auth.get_current_user")
    def test_list_transcripts_empty(
        self,
        mock_auth,
        client: TestClient,
        test_user: Profile,
        auth_headers: dict,
    ):
        """Test listing transcripts when none exist."""
        mock_auth.return_value = test_user

        response = client.get(
            "/api/v1/transcripts",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []
        assert data["total"] == 0

    @patch("app.middleware.auth.get_current_user")
    def test_upload_transcript(
        self,
        mock_auth,
        client: TestClient,
        test_user: Profile,
        auth_headers: dict,
        sample_transcript_content: str,
    ):
        """Test transcript upload."""
        mock_auth.return_value = test_user

        response = client.post(
            "/api/v1/transcripts/upload",
            headers=auth_headers,
            files={
                "file": ("test_meeting.txt", sample_transcript_content.encode(), "text/plain")
            },
            data={"idempotency_key": "test-upload-123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["filename"] == "test_meeting.txt"
        assert data["data"]["status"] == "uploaded"

    @patch("app.middleware.auth.get_current_user")
    def test_upload_duplicate_transcript(
        self,
        mock_auth,
        client: TestClient,
        db_session: Session,
        test_user: Profile,
        auth_headers: dict,
        sample_transcript_content: str,
    ):
        """Test duplicate transcript detection."""
        mock_auth.return_value = test_user

        # First upload
        response1 = client.post(
            "/api/v1/transcripts/upload",
            headers=auth_headers,
            files={
                "file": ("test.txt", sample_transcript_content.encode(), "text/plain")
            },
            data={"idempotency_key": "upload-1"},
        )
        assert response1.status_code == 200

        # Duplicate upload
        response2 = client.post(
            "/api/v1/transcripts/upload",
            headers=auth_headers,
            files={
                "file": ("test.txt", sample_transcript_content.encode(), "text/plain")
            },
            data={"idempotency_key": "upload-2"},
        )

        assert response2.status_code == 200
        data = response2.json()
        assert data["is_duplicate"] is True

    @patch("app.middleware.auth.get_current_user")
    def test_get_transcript(
        self,
        mock_auth,
        client: TestClient,
        db_session: Session,
        test_user: Profile,
        auth_headers: dict,
    ):
        """Test getting a specific transcript."""
        mock_auth.return_value = test_user

        # Create transcript
        import uuid
        import hashlib

        content = "Test transcript content"
        transcript = Transcript(
            id=uuid.uuid4(),
            user_id=test_user.id,
            filename="test.txt",
            file_type=".txt",
            size_bytes=len(content),
            content=content,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
            status=TranscriptStatus.UPLOADED,
        )
        db_session.add(transcript)
        db_session.commit()

        # Get transcript
        response = client.get(
            f"/api/v1/transcripts/{transcript.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["filename"] == "test.txt"

    @patch("app.middleware.auth.get_current_user")
    def test_delete_transcript(
        self,
        mock_auth,
        client: TestClient,
        db_session: Session,
        test_user: Profile,
        auth_headers: dict,
    ):
        """Test deleting a transcript."""
        mock_auth.return_value = test_user

        # Create transcript
        import uuid
        import hashlib

        content = "Delete me"
        transcript = Transcript(
            id=uuid.uuid4(),
            user_id=test_user.id,
            filename="delete_me.txt",
            file_type=".txt",
            size_bytes=len(content),
            content=content,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
            status=TranscriptStatus.UPLOADED,
        )
        db_session.add(transcript)
        db_session.commit()

        # Delete
        response = client.delete(
            f"/api/v1/transcripts/{transcript.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted
        deleted = db_session.query(Transcript).filter_by(id=transcript.id).first()
        assert deleted is None
