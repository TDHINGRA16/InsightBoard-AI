"""
Export service for JSON, CSV, and Gantt exports.
"""

import csv
import io
import json
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.task import Task
from app.models.transcript import Transcript
from app.schemas.export import ExportFormat, GanttExportData, GanttTask
from app.services.dependency_service import DependencyService
from app.services.graph_service import GraphService

logger = get_logger(__name__)


class ExportService:
    """
    Service for exporting transcript data in various formats.
    """

    def __init__(self, db: Session):
        """
        Initialize export service.

        Args:
            db: Database session
        """
        self.db = db
        self.dependency_service = DependencyService(db)
        self.graph_service = GraphService(db)

    def export_transcript(
        self,
        transcript_id: str,
        user_id: str,
        format: ExportFormat,
        include_dependencies: bool = True,
        include_graph: bool = False,
    ) -> Dict[str, Any]:
        """
        Export transcript data in requested format.

        Args:
            transcript_id: UUID of transcript
            user_id: UUID of requesting user (for logging)
            format: Export format (json, csv, gantt)
            include_dependencies: Include dependency data
            include_graph: Include graph layout data

        Returns:
            Dict with data, filename, and content_type

        Raises:
            NotFoundError: If transcript not found
        """
        # Shared workspace: any authenticated user can export any transcript
        transcript = (
            self.db.query(Transcript)
            .filter(Transcript.id == transcript_id)
            .first()
        )

        if not transcript:
            raise NotFoundError("Transcript", transcript_id)

        # Get tasks
        tasks = (
            self.db.query(Task)
            .filter(Task.transcript_id == transcript_id)
            .order_by(Task.created_at)
            .all()
        )

        # Get dependencies if requested
        dependencies = []
        if include_dependencies:
            dependencies = self.dependency_service.list_dependencies_for_transcript(
                transcript_id
            )

        if format == ExportFormat.JSON:
            return self._export_json(
                transcript, tasks, dependencies, include_graph
            )
        elif format == ExportFormat.CSV:
            return self._export_csv(transcript, tasks, dependencies)
        elif format == ExportFormat.GANTT:
            return self._export_gantt(transcript, transcript_id)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json(
        self,
        transcript: Transcript,
        tasks: List[Task],
        dependencies: List,
        include_graph: bool,
    ) -> Dict[str, Any]:
        """Export to JSON format."""
        data = {
            "transcript": {
                "id": str(transcript.id),
                "filename": transcript.filename,
                "created_at": transcript.created_at.isoformat(),
                "status": transcript.status.value,
            },
            "tasks": [
                {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "deadline": task.deadline.isoformat() if task.deadline else None,
                    "priority": task.priority.value,
                    "status": task.status.value,
                    "assignee": task.assignee,
                    "estimated_hours": task.estimated_hours,
                    "actual_hours": task.actual_hours,
                }
                for task in tasks
            ],
            "dependencies": [
                {
                    "id": str(dep.id),
                    "task_id": str(dep.task_id),
                    "depends_on_task_id": str(dep.depends_on_task_id),
                    "type": dep.dependency_type.value,
                    "lag_days": dep.lag_days,
                }
                for dep in dependencies
            ],
            "summary": {
                "total_tasks": len(tasks),
                "total_dependencies": len(dependencies),
                "tasks_by_status": self._count_by_status(tasks),
                "tasks_by_priority": self._count_by_priority(tasks),
            },
            "exported_at": datetime.utcnow().isoformat(),
        }

        if include_graph:
            graph_data, metrics = self.graph_service.generate_react_flow_data(
                str(transcript.id)
            )
            data["graph"] = graph_data.model_dump()
            data["metrics"] = metrics.model_dump()

        filename = f"{transcript.filename.rsplit('.', 1)[0]}_export.json"

        return {
            "data": data,
            "filename": filename,
            "content_type": "application/json",
        }

    def _export_csv(
        self,
        transcript: Transcript,
        tasks: List[Task],
        dependencies: List,
    ) -> Dict[str, Any]:
        """Export to CSV format."""
        # Build task ID to title mapping for dependencies
        task_titles = {str(task.id): task.title for task in tasks}

        # Build dependency info per task
        task_deps: Dict[str, List[str]] = {}
        for dep in dependencies:
            task_id = str(dep.task_id)
            depends_on = task_titles.get(str(dep.depends_on_task_id), "Unknown")
            if task_id not in task_deps:
                task_deps[task_id] = []
            task_deps[task_id].append(depends_on)

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "ID",
            "Title",
            "Description",
            "Deadline",
            "Priority",
            "Status",
            "Assignee",
            "Estimated Hours",
            "Actual Hours",
            "Dependencies",
        ])

        # Data rows
        for task in tasks:
            deps = task_deps.get(str(task.id), [])
            writer.writerow([
                str(task.id),
                task.title,
                task.description or "",
                task.deadline.isoformat() if task.deadline else "",
                task.priority.value,
                task.status.value,
                task.assignee or "",
                task.estimated_hours or "",
                task.actual_hours or "",
                "; ".join(deps),
            ])

        csv_data = output.getvalue()
        filename = f"{transcript.filename.rsplit('.', 1)[0]}_export.csv"

        return {
            "data": csv_data,
            "filename": filename,
            "content_type": "text/csv",
        }

    def _export_gantt(
        self,
        transcript: Transcript,
        transcript_id: str,
    ) -> Dict[str, Any]:
        """Export to Gantt chart format."""
        gantt_tasks = self.graph_service.generate_gantt_data(transcript_id)

        data = GanttExportData(
            project_name=transcript.filename,
            start_date=datetime.utcnow().isoformat(),
            tasks=[GanttTask(**task) for task in gantt_tasks],
        )

        filename = f"{transcript.filename.rsplit('.', 1)[0]}_gantt.json"

        return {
            "data": data.model_dump(),
            "filename": filename,
            "content_type": "application/json",
        }

    def _count_by_status(self, tasks: List[Task]) -> Dict[str, int]:
        """Count tasks by status."""
        counts: Dict[str, int] = {}
        for task in tasks:
            status = task.status.value
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _count_by_priority(self, tasks: List[Task]) -> Dict[str, int]:
        """Count tasks by priority."""
        counts: Dict[str, int] = {}
        for task in tasks:
            priority = task.priority.value
            counts[priority] = counts.get(priority, 0) + 1
        return counts
