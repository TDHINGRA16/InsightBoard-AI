"""
Tests for dependency service and graph algorithms.
"""

import pytest
import networkx as nx
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.task import Task, TaskPriority, TaskStatus
from app.models.transcript import Transcript, TranscriptStatus
from app.models.dependency import Dependency, DependencyType
from app.models.user import Profile
from app.services.dependency_service import DependencyService
from app.core.exceptions import CyclicDependencyError, ValidationError


class TestDependencyService:
    """Tests for dependency service."""

    @pytest.fixture
    def transcript(self, db_session: Session, test_user: Profile) -> Transcript:
        """Create test transcript."""
        import hashlib

        content = "Test transcript"
        transcript = Transcript(
            id=uuid4(),
            user_id=test_user.id,
            filename="test.txt",
            file_type=".txt",
            size_bytes=len(content),
            content=content,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
            status=TranscriptStatus.ANALYZED,
        )
        db_session.add(transcript)
        db_session.commit()
        return transcript

    @pytest.fixture
    def tasks(
        self,
        db_session: Session,
        transcript: Transcript,
    ) -> list[Task]:
        """Create test tasks."""
        tasks = []
        for i in range(5):
            task = Task(
                id=uuid4(),
                transcript_id=transcript.id,
                title=f"Task {i + 1}",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                estimated_hours=4,
            )
            db_session.add(task)
            tasks.append(task)

        db_session.commit()
        return tasks

    def test_create_dependency(
        self,
        db_session: Session,
        tasks: list[Task],
    ):
        """Test creating a valid dependency."""
        service = DependencyService(db_session)

        dep = service.create_dependency(
            task_id=str(tasks[1].id),
            depends_on_task_id=str(tasks[0].id),
        )

        assert dep is not None
        assert str(dep.task_id) == str(tasks[1].id)
        assert str(dep.depends_on_task_id) == str(tasks[0].id)

    def test_self_dependency_fails(
        self,
        db_session: Session,
        tasks: list[Task],
    ):
        """Test that self-dependency is rejected."""
        service = DependencyService(db_session)

        with pytest.raises(ValidationError):
            service.create_dependency(
                task_id=str(tasks[0].id),
                depends_on_task_id=str(tasks[0].id),
            )

    def test_cycle_detection(
        self,
        db_session: Session,
        tasks: list[Task],
    ):
        """Test that cyclic dependencies are detected."""
        service = DependencyService(db_session)

        # Create chain: Task0 -> Task1 -> Task2
        service.create_dependency(
            task_id=str(tasks[1].id),
            depends_on_task_id=str(tasks[0].id),
            validate_dag=True,
        )
        service.create_dependency(
            task_id=str(tasks[2].id),
            depends_on_task_id=str(tasks[1].id),
            validate_dag=True,
        )

        # Try to create cycle: Task0 -> Task2 (would complete cycle)
        with pytest.raises(CyclicDependencyError):
            service.create_dependency(
                task_id=str(tasks[0].id),
                depends_on_task_id=str(tasks[2].id),
                validate_dag=True,
            )

    def test_build_dependency_graph(
        self,
        db_session: Session,
        tasks: list[Task],
    ):
        """Test building NetworkX graph."""
        service = DependencyService(db_session)

        # Create dependencies
        service.create_dependency(
            task_id=str(tasks[1].id),
            depends_on_task_id=str(tasks[0].id),
            validate_dag=False,
        )
        service.create_dependency(
            task_id=str(tasks[2].id),
            depends_on_task_id=str(tasks[1].id),
            validate_dag=False,
        )

        transcript_id = str(tasks[0].transcript_id)
        graph = service.build_dependency_graph(transcript_id)

        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_nodes() == 5
        assert graph.number_of_edges() == 2

    def test_validate_dag(
        self,
        db_session: Session,
        tasks: list[Task],
    ):
        """Test DAG validation."""
        service = DependencyService(db_session)

        # Create valid DAG
        service.create_dependency(
            task_id=str(tasks[1].id),
            depends_on_task_id=str(tasks[0].id),
            validate_dag=False,
        )

        transcript_id = str(tasks[0].transcript_id)
        is_valid, cycle = service.validate_dag(transcript_id)

        assert is_valid is True
        assert cycle is None

    def test_compute_critical_path(
        self,
        db_session: Session,
        tasks: list[Task],
    ):
        """Test critical path computation."""
        service = DependencyService(db_session)

        # Create linear chain: Task0 -> Task1 -> Task2
        service.create_dependency(
            task_id=str(tasks[1].id),
            depends_on_task_id=str(tasks[0].id),
            validate_dag=False,
        )
        service.create_dependency(
            task_id=str(tasks[2].id),
            depends_on_task_id=str(tasks[1].id),
            validate_dag=False,
        )

        transcript_id = str(tasks[0].transcript_id)
        graph = service.build_dependency_graph(transcript_id)

        critical_path, total_duration, slack = service.compute_critical_path(graph)

        assert len(critical_path) >= 1
        assert total_duration > 0
        assert isinstance(slack, dict)

    def test_detect_bottlenecks(
        self,
        db_session: Session,
        tasks: list[Task],
    ):
        """Test bottleneck detection."""
        service = DependencyService(db_session)

        # Create star pattern: Task0 is bottleneck
        for i in range(1, 4):
            service.create_dependency(
                task_id=str(tasks[i].id),
                depends_on_task_id=str(tasks[0].id),
                validate_dag=False,
            )

        transcript_id = str(tasks[0].transcript_id)
        graph = service.build_dependency_graph(transcript_id)

        bottlenecks = service.detect_bottlenecks(graph, top_n=3)

        assert len(bottlenecks) > 0
        # Task 0 should have highest score (out_degree = 3)
        assert bottlenecks[0]["out_degree"] >= 3

    def test_delete_dependency(
        self,
        db_session: Session,
        tasks: list[Task],
    ):
        """Test deleting a dependency."""
        service = DependencyService(db_session)

        dep = service.create_dependency(
            task_id=str(tasks[1].id),
            depends_on_task_id=str(tasks[0].id),
            validate_dag=False,
        )

        result = service.delete_dependency(str(dep.id))
        assert result is True

        # Verify deleted
        deleted = (
            db_session.query(Dependency)
            .filter_by(id=dep.id)
            .first()
        )
        assert deleted is None
