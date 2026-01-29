"""
Background tasks for RQ workers.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.logging import get_logger
from app.database import SessionLocal
from app.models.job import Job, JobStatus, JobType
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.transcript import Transcript, TranscriptStatus
from app.services.cache_service import cache_service
from app.services.dependency_service import DependencyService
from app.services.graph_service import GraphService
from app.services.nlp_service import nlp_service
from app.services.webhook_service import trigger_analysis_completed
from app.utils.formatting import normalize_date

logger = get_logger(__name__)


def analyze_transcript_job(
    transcript_id: str,
    user_id: str,
    job_id: str,
) -> dict:
    """
    Background job to analyze a transcript with LLM.

    This job:
    1. Updates job status to processing
    2. Fetches transcript content
    3. Calls LLM to extract tasks and dependencies
    4. Creates task and dependency records
    5. Builds dependency graph and validates DAG
    6. Computes critical path
    7. Caches results
    8. Triggers webhooks

    Args:
        transcript_id: UUID of transcript to analyze
        user_id: UUID of requesting user
        job_id: Job ID for status updates

    Returns:
        dict: Analysis result summary
    """
    logger.info(f"Starting analysis job {job_id} for transcript {transcript_id}")

    db = SessionLocal()
    try:
        # Update job status
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            job.progress = 10
            db.commit()

        # Update transcript status
        transcript = (
            db.query(Transcript)
            .filter(Transcript.id == transcript_id)
            .first()
        )

        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")

        transcript.status = TranscriptStatus.ANALYZING
        db.commit()

        # Remove any existing tasks/dependencies for this transcript so
        # re-analysis replaces previous extraction instead of appending.
        try:
            existing_count = db.query(Task).filter(Task.transcript_id == transcript_id).count()
            if existing_count:
                logger.info(
                    f"Deleting {existing_count} existing tasks (and cascaded dependencies) for transcript {transcript_id}"
                )
                # Bulk delete tasks; DB-level ON DELETE CASCADE will remove dependencies.
                db.query(Task).filter(Task.transcript_id == transcript_id).delete(synchronize_session=False)
                db.commit()
        except Exception as e:
            logger.warning(f"Failed to clear existing tasks for transcript {transcript_id}: {e}")
        # Progress: Fetched transcript
        _update_progress(db, job_id, 20)

        # Call LLM to extract tasks
        logger.info("Calling NLP service for task extraction")
        extraction_result = nlp_service.extract_tasks_and_dependencies(
            transcript.content
        )

        # Progress: LLM completed
        _update_progress(db, job_id, 50)

        # Create tasks
        tasks_data = extraction_result.get("tasks", [])
        task_title_to_id = {}
        created_tasks = []

        for task_data in tasks_data:
            # Parse deadline
            deadline = normalize_date(task_data.get("deadline"))

            # Map priority
            priority_str = task_data.get("priority", "medium").lower()
            priority_map = {
                "low": TaskPriority.LOW,
                "medium": TaskPriority.MEDIUM,
                "high": TaskPriority.HIGH,
                "critical": TaskPriority.CRITICAL,
            }
            priority = priority_map.get(priority_str, TaskPriority.MEDIUM)

            task = Task(
                transcript_id=transcript_id,
                title=task_data.get("title", "Untitled Task"),
                description=task_data.get("description"),
                deadline=deadline,
                priority=priority,
                status=TaskStatus.PENDING,
                assignee=task_data.get("assignee"),
                estimated_hours=task_data.get("estimated_hours", 4),
            )

            db.add(task)
            db.flush()  # Get ID without committing

            task_title_to_id[task.title.lower()] = str(task.id)
            created_tasks.append(task)

        db.commit()
        logger.info(f"Created {len(created_tasks)} tasks")
        
        # Log task titles for debugging dependency matching
        logger.debug(f"Task title mapping: {list(task_title_to_id.keys())}")

        # Progress: Tasks created
        _update_progress(db, job_id, 70)

        # Create dependencies
        dependencies_data = extraction_result.get("dependencies", [])
        logger.info(f"LLM extracted {len(dependencies_data)} raw dependencies")
        
        # Log raw dependency data for debugging
        for dep in dependencies_data:
            logger.debug(f"Raw dependency: {dep}")
        
        dependency_service = DependencyService(db)

        created_deps = dependency_service.bulk_create_dependencies(
            dependencies_data,
            task_title_to_id,
        )

        logger.info(f"Successfully created {len(created_deps)} dependencies in database")

        # Progress: Dependencies created
        _update_progress(db, job_id, 80)

        # Validate DAG
        is_valid, cycle = dependency_service.validate_dag(transcript_id)

        cycle_task_ids = []
        blocked_task_count = 0
        if not is_valid:
            logger.warning(f"Cyclic dependencies detected: {cycle}")
            # Mark tasks participating in the cycle as BLOCKED in DB.
            # (We keep transcript analysis as "analyzed" but include diagnostics.)
            if cycle:
                try:
                    cycle_task_ids = [UUID(task_id) for task_id in cycle]
                    blocked_task_count = (
                        db.query(Task)
                        .filter(
                            Task.transcript_id == transcript_id,
                            Task.id.in_(cycle_task_ids),
                        )
                        .update(
                            {Task.status: TaskStatus.BLOCKED},
                            synchronize_session=False,
                        )
                    )
                    db.commit()
                except Exception as e:
                    logger.warning(f"Failed to mark cycle tasks as blocked: {e}")
                    db.rollback()

        # Build graph and compute metrics
        graph_service = GraphService(db)
        nx_graph = dependency_service.build_dependency_graph(transcript_id)

        critical_path = []
        critical_path_length = 0
        slack = {}

        if is_valid and nx_graph.nodes():
            critical_path, critical_path_length, slack = (
                dependency_service.compute_critical_path(nx_graph)
            )

        # Generate and save React Flow data
        graph_data, metrics = graph_service.generate_react_flow_data(
            transcript_id,
            critical_path=critical_path,
        )

        graph_service.save_graph(
            transcript_id=transcript_id,
            graph_data=graph_data,
            metrics=metrics,
            critical_path=critical_path,
            critical_path_length=critical_path_length,
            slack_data=slack,
        )

        # Progress: Graph built
        _update_progress(db, job_id, 90)

        # Build result summary
        result = {
            "task_count": len(created_tasks),
            "dependency_count": len(created_deps),
            "critical_path_length": critical_path_length,
            "is_valid_dag": is_valid,
            "warning": None if is_valid else "Cyclic dependencies detected",
            "cycle": cycle if not is_valid else None,
            "cycle_task_ids": [str(tid) for tid in cycle_task_ids] if cycle_task_ids else [],
            "blocked_task_count": blocked_task_count,
        }

        # Cache analysis result
        cache_service.cache_analysis(transcript_id, result)

        # Update transcript status (clear any previous error)
        transcript.status = TranscriptStatus.ANALYZED
        transcript.analysis_result = result
        transcript.error_message = None  # Clear stale error from previous failed attempts
        db.commit()

        # Update job as completed
        if job:
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.completed_at = datetime.utcnow()
            job.result = result
            db.commit()

        logger.info(f"Analysis completed for transcript {transcript_id}")

        # Trigger webhooks
        try:
            trigger_analysis_completed(
                db,
                user_id,
                transcript_id,
                len(created_tasks),
                len(created_deps),
            )
        except Exception as e:
            logger.error(f"Webhook trigger failed: {e}")

        return result

    except Exception as e:
        logger.exception(f"Analysis job failed: {e}")

        # Update job as failed
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()

            transcript = (
                db.query(Transcript)
                .filter(Transcript.id == transcript_id)
                .first()
            )
            if transcript:
                transcript.status = TranscriptStatus.FAILED
                transcript.error_message = str(e)
                db.commit()
        except Exception:
            pass

        raise

    finally:
        db.close()


def export_data_job(
    transcript_id: str,
    user_id: str,
    job_id: str,
    format: str,
) -> dict:
    """
    Background job to export transcript data.

    Args:
        transcript_id: UUID of transcript
        user_id: UUID of user
        job_id: Job ID
        format: Export format (json, csv, gantt)

    Returns:
        dict: Export result with data URL or inline data
    """
    logger.info(f"Starting export job {job_id} for transcript {transcript_id}")

    db = SessionLocal()
    try:
        from app.services.export_service import ExportService
        from app.schemas.export import ExportFormat

        # Update job status
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            db.commit()

        # Perform export
        export_service = ExportService(db)
        export_format = ExportFormat(format)

        result = export_service.export_transcript(
            transcript_id=transcript_id,
            user_id=user_id,
            format=export_format,
            include_dependencies=True,
            include_graph=True,
        )

        # Update job as completed
        if job:
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.completed_at = datetime.utcnow()
            job.result = {
                "filename": result["filename"],
                "content_type": result["content_type"],
                "format": format,
            }
            db.commit()

        logger.info(f"Export completed: {result['filename']}")
        return result

    except Exception as e:
        logger.exception(f"Export job failed: {e}")

        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass

        raise

    finally:
        db.close()


def _update_progress(db, job_id: str, progress: int) -> None:
    """Update job progress."""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.progress = progress
            db.commit()
    except Exception as e:
        logger.warning(f"Failed to update progress: {e}")
