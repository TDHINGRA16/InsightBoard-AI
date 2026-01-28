"""
Dependency service for DAG building, validation, and graph algorithms.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

import networkx as nx
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import CyclicDependencyError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.dependency import Dependency, DependencyType
from app.models.task import Task
from app.models.transcript import Transcript

logger = get_logger(__name__)


class DependencyService:
    """
    Service for dependency operations and graph algorithms.

    Handles DAG construction, validation, cycle detection, and path analysis.
    """

    def __init__(self, db: Session):
        """
        Initialize dependency service.

        Args:
            db: Database session
        """
        self.db = db

    def create_dependency(
        self,
        task_id: str,
        depends_on_task_id: str,
        dependency_type: DependencyType = DependencyType.BLOCKS,
        lag_days: int = 0,
        validate_dag: bool = True,
    ) -> Dependency:
        """
        Create a new dependency between tasks.

        Args:
            task_id: UUID of dependent task
            depends_on_task_id: UUID of prerequisite task
            dependency_type: Type of dependency
            lag_days: Days between completion and start
            validate_dag: Whether to validate DAG after creation

        Returns:
            Dependency: Created dependency

        Raises:
            ValidationError: If self-dependency or duplicate
            CyclicDependencyError: If dependency would create a cycle
        """
        # Validate no self-dependency
        if task_id == depends_on_task_id:
            raise ValidationError("A task cannot depend on itself")

        # Check tasks exist and belong to same transcript
        task = self.db.query(Task).filter(Task.id == task_id).first()
        depends_on = self.db.query(Task).filter(Task.id == depends_on_task_id).first()

        if not task:
            raise NotFoundError("Task", task_id)
        if not depends_on:
            raise NotFoundError("Task", depends_on_task_id)
        if task.transcript_id != depends_on.transcript_id:
            raise ValidationError("Dependencies must be between tasks in the same transcript")

        # Check for existing dependency
        existing = (
            self.db.query(Dependency)
            .filter(
                Dependency.task_id == task_id,
                Dependency.depends_on_task_id == depends_on_task_id,
            )
            .first()
        )

        if existing:
            raise ValidationError("This dependency already exists")

        # Validate DAG if requested
        if validate_dag:
            # Build graph with proposed dependency
            graph = self.build_dependency_graph(str(task.transcript_id))
            graph.add_edge(depends_on_task_id, task_id)

            if not nx.is_directed_acyclic_graph(graph):
                cycles = list(nx.simple_cycles(graph))
                raise CyclicDependencyError(cycles[0] if cycles else [])

        # Create dependency
        dependency = Dependency(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
            dependency_type=dependency_type,
            lag_days=lag_days,
        )

        self.db.add(dependency)
        self.db.commit()
        self.db.refresh(dependency)

        logger.info(f"Created dependency: {depends_on_task_id} -> {task_id}")
        return dependency

    def delete_dependency(self, dependency_id: str) -> bool:
        """
        Delete a dependency.

        Args:
            dependency_id: UUID of dependency

        Returns:
            bool: True if deleted

        Raises:
            NotFoundError: If dependency not found
        """
        dependency = (
            self.db.query(Dependency)
            .filter(Dependency.id == dependency_id)
            .first()
        )

        if not dependency:
            raise NotFoundError("Dependency", dependency_id)

        self.db.delete(dependency)
        self.db.commit()

        logger.info(f"Deleted dependency: {dependency_id}")
        return True

    def get_task_dependencies(
        self,
        task_id: str,
    ) -> Tuple[List[Dependency], List[Dependency]]:
        """
        Get dependencies and dependents for a task.

        Args:
            task_id: UUID of task

        Returns:
            Tuple[List[Dependency], List[Dependency]]: (dependencies, dependents)
        """
        # Tasks this task depends on
        dependencies = (
            self.db.query(Dependency)
            .options(joinedload(Dependency.depends_on_task))
            .filter(Dependency.task_id == task_id)
            .all()
        )

        # Tasks that depend on this task
        dependents = (
            self.db.query(Dependency)
            .options(joinedload(Dependency.task))
            .filter(Dependency.depends_on_task_id == task_id)
            .all()
        )

        return dependencies, dependents

    def list_dependencies_for_transcript(
        self,
        transcript_id: str,
    ) -> List[Dependency]:
        """
        List all dependencies for a transcript.

        Args:
            transcript_id: UUID of transcript

        Returns:
            List[Dependency]: All dependencies in transcript
        """
        # Get all task IDs for transcript
        task_ids = (
            self.db.query(Task.id)
            .filter(Task.transcript_id == transcript_id)
            .all()
        )
        task_id_set = {str(t[0]) for t in task_ids}

        if not task_id_set:
            return []

        # Get dependencies between these tasks
        dependencies = (
            self.db.query(Dependency)
            .options(
                joinedload(Dependency.task),
                joinedload(Dependency.depends_on_task),
            )
            .filter(Dependency.task_id.in_(task_id_set))
            .all()
        )

        return dependencies

    def list_dependencies_for_user(self, user_id: str) -> List[Dependency]:
        """
        List all dependencies across all transcripts owned by a user.

        Args:
            user_id: UUID of the user

        Returns:
            List[Dependency]: Dependencies with loaded task titles
        """
        return (
            self.db.query(Dependency)
            .join(Task, Dependency.task_id == Task.id)
            .join(Transcript, Task.transcript_id == Transcript.id)
            .options(
                joinedload(Dependency.task),
                joinedload(Dependency.depends_on_task),
            )
            .filter(Transcript.user_id == user_id)
            .all()
        )

    def build_dependency_graph(
        self,
        transcript_id: str,
    ) -> nx.DiGraph:
        """
        Build a NetworkX DiGraph from transcript tasks and dependencies.

        Args:
            transcript_id: UUID of transcript

        Returns:
            nx.DiGraph: Dependency graph
        """
        # Get tasks
        tasks = (
            self.db.query(Task)
            .filter(Task.transcript_id == transcript_id)
            .all()
        )

        # Create graph
        graph = nx.DiGraph()

        # Add nodes with attributes
        for task in tasks:
            graph.add_node(
                str(task.id),
                title=task.title,
                priority=task.priority.value,
                status=task.status.value,
                duration=task.estimated_hours or 4,
                assignee=task.assignee,
                deadline=task.deadline.isoformat() if task.deadline else None,
            )

        # Get dependencies
        dependencies = self.list_dependencies_for_transcript(transcript_id)

        # Add edges (direction: prerequisite -> dependent)
        for dep in dependencies:
            graph.add_edge(
                str(dep.depends_on_task_id),
                str(dep.task_id),
                type=dep.dependency_type.value,
                lag=dep.lag_days,
            )

        return graph

    def validate_dag(self, transcript_id: str) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate that the dependency graph is a DAG.

        Args:
            transcript_id: UUID of transcript

        Returns:
            Tuple[bool, Optional[List[str]]]: (is_valid, cycle if found)
        """
        graph = self.build_dependency_graph(transcript_id)

        if nx.is_directed_acyclic_graph(graph):
            return True, None

        # Find cycles
        try:
            cycles = list(nx.simple_cycles(graph))
            if cycles:
                return False, cycles[0]
        except nx.NetworkXError:
            pass

        return False, []

    def compute_critical_path(
        self,
        graph: nx.DiGraph,
    ) -> Tuple[List[str], float, Dict[str, float]]:
        """
        Compute the critical path using CPM.

        Args:
            graph: NetworkX DiGraph with duration attributes

        Returns:
            Tuple containing:
                - List of task IDs on critical path
                - Total duration
                - Dict of slack per task
        """
        if not graph.nodes():
            return [], 0, {}

        # Check if DAG
        if not nx.is_directed_acyclic_graph(graph):
            raise CyclicDependencyError([])

        # Get topological order
        topo_order = list(nx.topological_sort(graph))

        # Forward pass: compute earliest start/finish
        earliest_start: Dict[str, float] = {}
        earliest_finish: Dict[str, float] = {}

        for node in topo_order:
            duration = graph.nodes[node].get("duration", 4)

            # Get max finish time of predecessors
            predecessors = list(graph.predecessors(node))
            if not predecessors:
                earliest_start[node] = 0
            else:
                earliest_start[node] = max(
                    earliest_finish.get(p, 0) for p in predecessors
                )

            earliest_finish[node] = earliest_start[node] + duration

        # Total project duration
        if earliest_finish:
            total_duration = max(earliest_finish.values())
        else:
            total_duration = 0

        # Backward pass: compute latest start/finish
        latest_finish: Dict[str, float] = {}
        latest_start: Dict[str, float] = {}

        for node in reversed(topo_order):
            duration = graph.nodes[node].get("duration", 4)

            # Get min start time of successors
            successors = list(graph.successors(node))
            if not successors:
                latest_finish[node] = total_duration
            else:
                latest_finish[node] = min(
                    latest_start.get(s, total_duration) for s in successors
                )

            latest_start[node] = latest_finish[node] - duration

        # Compute slack and identify critical path
        slack: Dict[str, float] = {}
        critical_nodes: List[str] = []

        for node in topo_order:
            node_slack = latest_start[node] - earliest_start[node]
            slack[node] = max(0, round(node_slack, 2))

            if node_slack <= 0.001:  # Account for floating point
                critical_nodes.append(node)

        logger.info(
            f"Critical path: {len(critical_nodes)} tasks, "
            f"duration: {total_duration} hours"
        )

        return critical_nodes, total_duration, slack

    def detect_bottlenecks(
        self,
        graph: nx.DiGraph,
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Detect bottleneck tasks based on connectivity.

        Args:
            graph: NetworkX DiGraph
            top_n: Number of bottlenecks to return

        Returns:
            List of bottleneck info dicts
        """
        if not graph.nodes():
            return []

        bottlenecks = []

        for node in graph.nodes():
            in_degree = graph.in_degree(node)
            out_degree = graph.out_degree(node)

            # Score based on connectivity (more connections = more bottleneck)
            score = out_degree * 2 + in_degree

            if score > 0:
                bottlenecks.append({
                    "task_id": node,
                    "task_title": graph.nodes[node].get("title", "Unknown"),
                    "score": score,
                    "in_degree": in_degree,
                    "out_degree": out_degree,
                })

        # Sort by score descending
        bottlenecks.sort(key=lambda x: x["score"], reverse=True)

        return bottlenecks[:top_n]

    def bulk_create_dependencies(
        self,
        dependencies_data: List[Dict[str, Any]],
        task_title_to_id: Dict[str, str],
    ) -> List[Dependency]:
        """
        Bulk create dependencies from LLM extraction.

        Args:
            dependencies_data: List of dependency dicts with titles
            task_title_to_id: Mapping from task title to ID

        Returns:
            List[Dependency]: Created dependencies
        """
        created = []

        for dep_data in dependencies_data:
            task_title = dep_data.get("task_title", "")
            depends_on_title = dep_data.get("depends_on_title", "")

            # Look up IDs
            task_id = task_title_to_id.get(task_title.lower())
            depends_on_id = task_title_to_id.get(depends_on_title.lower())

            if not task_id or not depends_on_id:
                logger.warning(f"Could not find tasks for dependency: {dep_data}")
                continue

            if task_id == depends_on_id:
                continue

            # Check for existing
            existing = (
                self.db.query(Dependency)
                .filter(
                    Dependency.task_id == task_id,
                    Dependency.depends_on_task_id == depends_on_id,
                )
                .first()
            )

            if existing:
                continue

            dependency = Dependency(
                task_id=task_id,
                depends_on_task_id=depends_on_id,
                dependency_type=DependencyType.BLOCKS,
                lag_days=0,
            )

            self.db.add(dependency)
            created.append(dependency)

        if created:
            self.db.commit()

        logger.info(f"Bulk created {len(created)} dependencies")
        return created
