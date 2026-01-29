"""
Graph service for React Flow visualization and graph metrics.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.graph import Graph
from app.models.task import Task
from app.schemas.graph import (
    GraphData,
    GraphMetrics,
    ReactFlowEdge,
    ReactFlowNode,
    ReactFlowNodeData,
    ReactFlowNodePosition,
)
from app.services.dependency_service import DependencyService

logger = get_logger(__name__)


class GraphService:
    """
    Service for graph visualization and metrics.

    Converts NetworkX graphs to React Flow format and computes metrics.
    """

    def __init__(self, db: Session):
        """
        Initialize graph service.

        Args:
            db: Database session
        """
        self.db = db
        self.dependency_service = DependencyService(db)

    def generate_react_flow_data(
        self,
        transcript_id: str,
        critical_path: Optional[List[str]] = None,
    ) -> Tuple[GraphData, GraphMetrics]:
        """
        Generate React Flow compatible graph data.

        Args:
            transcript_id: UUID of transcript
            critical_path: Optional list of task IDs on critical path

        Returns:
            Tuple[GraphData, GraphMetrics]: Graph data and metrics
        """
        # Build NetworkX graph
        nx_graph = self.dependency_service.build_dependency_graph(transcript_id)

        if not nx_graph.nodes():
            return (
                GraphData(nodes=[], edges=[]),
                GraphMetrics(nodes_count=0, edges_count=0, dependencies_avg=0),
            )

        # Compute layout positions
        positions = self._compute_layout(nx_graph)

        # Create set for critical path lookup
        critical_set = set(critical_path or [])

        # Convert nodes to React Flow format
        nodes: List[ReactFlowNode] = []
        for node_id in nx_graph.nodes():
            node_data = nx_graph.nodes[node_id]
            pos = positions.get(node_id, (0, 0))

            nodes.append(
                ReactFlowNode(
                    id=node_id,
                    type="taskNode",
                    data=ReactFlowNodeData(
                        label=node_data.get("title", "Unknown")[:50],
                        title=node_data.get("title", "Unknown"),
                        description=node_data.get("description"),
                        priority=node_data.get("priority", "medium"),
                        status=node_data.get("status", "pending"),
                        assignee=node_data.get("assignee"),
                        duration=node_data.get("duration", 4),
                        deadline=node_data.get("deadline"),
                        is_critical=node_id in critical_set,
                    ),
                    position=ReactFlowNodePosition(x=pos[0], y=pos[1]),
                )
            )

        # Convert edges to React Flow format
        edges: List[ReactFlowEdge] = []
        for source, target in nx_graph.edges():
            edge_data = nx_graph.edges[source, target]
            is_critical = source in critical_set and target in critical_set

            edges.append(
                ReactFlowEdge(
                    id=f"{source}-{target}",
                    source=source,
                    target=target,
                    label=edge_data.get("type", "blocks"),
                    animated=is_critical,
                    type="smoothstep",
                    style={
                        "stroke": "#ef4444" if is_critical else "#6b7280",
                        "strokeWidth": 2 if is_critical else 1,
                    },
                )
            )

        # Compute metrics
        nodes_count = nx_graph.number_of_nodes()
        edges_count = nx_graph.number_of_edges()
        dependencies_avg = edges_count / nodes_count if nodes_count > 0 else 0

        metrics = GraphMetrics(
            nodes_count=nodes_count,
            edges_count=edges_count,
            dependencies_avg=round(dependencies_avg, 2),
        )

        return GraphData(nodes=nodes, edges=edges), metrics

    def _compute_layout(
        self,
        graph: nx.DiGraph,
        width: float = 2000,  # Increased from 1200 for more spacing
        height: float = 1200,  # Increased from 800 for more spacing
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute node positions for visualization.

        Uses a hierarchical layout based on topological order.

        Args:
            graph: NetworkX DiGraph
            width: Canvas width
            height: Canvas height

        Returns:
            Dict mapping node IDs to (x, y) positions
        """
        if not graph.nodes():
            return {}

        # Try hierarchical layout for DAGs
        if nx.is_directed_acyclic_graph(graph):
            return self._hierarchical_layout(graph, width, height)

        # Fall back to spring layout with more spacing
        try:
            pos = nx.spring_layout(graph, k=3, iterations=50, seed=42)  # k=3 for more spacing
            return {
                node: (p[0] * width / 2 + width / 2, p[1] * height / 2 + height / 2)
                for node, p in pos.items()
            }
        except Exception:
            # Default grid layout
            return self._grid_layout(graph, width, height)

    def _hierarchical_layout(
        self,
        graph: nx.DiGraph,
        width: float,
        height: float,
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute hierarchical layout based on topological order.

        Args:
            graph: NetworkX DiGraph (must be DAG)
            width: Canvas width
            height: Canvas height

        Returns:
            Dict mapping node IDs to (x, y) positions
        """
        # Compute levels based on longest path to root
        levels: Dict[str, int] = {}

        for node in nx.topological_sort(graph):
            predecessors = list(graph.predecessors(node))
            if not predecessors:
                levels[node] = 0
            else:
                levels[node] = max(levels[p] for p in predecessors) + 1

        # Group nodes by level
        nodes_by_level: Dict[int, List[str]] = {}
        for node, level in levels.items():
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)

        # Compute positions with more generous spacing
        positions: Dict[str, Tuple[float, float]] = {}
        max_level = max(levels.values()) if levels else 0
        
        # Use fixed spacing rather than percentage-based
        vertical_spacing = 200  # pixels between levels
        horizontal_spacing = 350  # pixels between nodes in same level
        start_x = 150
        start_y = 100

        for level, nodes in nodes_by_level.items():
            y = start_y + level * vertical_spacing

            for i, node in enumerate(nodes):
                # Center nodes in their level
                total_width = (len(nodes) - 1) * horizontal_spacing
                x = start_x + (width - total_width) / 2 + i * horizontal_spacing
                positions[node] = (x, y)

        return positions

    def _grid_layout(
        self,
        graph: nx.DiGraph,
        width: float,
        height: float,
    ) -> Dict[str, Tuple[float, float]]:
        """
        Simple grid layout fallback.

        Args:
            graph: NetworkX DiGraph
            width: Canvas width
            height: Canvas height

        Returns:
            Dict mapping node IDs to (x, y) positions
        """
        nodes = list(graph.nodes())
        n = len(nodes)

        if n == 0:
            return {}

        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

        positions = {}
        for i, node in enumerate(nodes):
            row = i // cols
            col = i % cols
            x = 100 + col * (width - 200) / max(cols - 1, 1)
            y = 100 + row * (height - 200) / max(rows - 1, 1)
            positions[node] = (x, y)

        return positions

    def save_graph(
        self,
        transcript_id: str,
        graph_data: GraphData,
        metrics: GraphMetrics,
        critical_path: Optional[List[str]] = None,
        critical_path_length: Optional[float] = None,
        slack_data: Optional[Dict[str, float]] = None,
    ) -> Graph:
        """
        Save or update graph data for a transcript.

        Args:
            transcript_id: UUID of transcript
            graph_data: React Flow graph data
            metrics: Graph metrics
            critical_path: Optional critical path task IDs
            critical_path_length: Optional critical path duration
            slack_data: Optional slack per task

        Returns:
            Graph: Saved graph record
        """
        # Check for existing graph
        graph = (
            self.db.query(Graph)
            .filter(Graph.transcript_id == transcript_id)
            .first()
        )

        if graph:
            # Update existing
            graph.nodes_count = metrics.nodes_count
            graph.edges_count = metrics.edges_count
            graph.critical_path = critical_path
            graph.critical_path_length = critical_path_length
            graph.slack_data = slack_data
            graph.graph_data = graph_data.model_dump()
        else:
            # Create new
            graph = Graph(
                transcript_id=transcript_id,
                nodes_count=metrics.nodes_count,
                edges_count=metrics.edges_count,
                critical_path=critical_path,
                critical_path_length=critical_path_length,
                slack_data=slack_data,
                graph_data=graph_data.model_dump(),
            )
            self.db.add(graph)

        self.db.commit()
        self.db.refresh(graph)

        logger.info(f"Saved graph for transcript: {transcript_id}")
        return graph

    def get_graph(self, transcript_id: str) -> Optional[Graph]:
        """
        Get saved graph for a transcript.

        Args:
            transcript_id: UUID of transcript

        Returns:
            Optional[Graph]: Graph record if exists
        """
        return (
            self.db.query(Graph)
            .filter(Graph.transcript_id == transcript_id)
            .first()
        )

    def generate_gantt_data(
        self,
        transcript_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate Gantt chart data from tasks.

        Args:
            transcript_id: UUID of transcript

        Returns:
            List of Gantt task dicts
        """
        from datetime import datetime, timedelta

        tasks = (
            self.db.query(Task)
            .filter(Task.transcript_id == transcript_id)
            .all()
        )

        # Get dependencies
        nx_graph = self.dependency_service.build_dependency_graph(transcript_id)

        # Compute start dates based on dependencies
        start_dates: Dict[str, datetime] = {}
        project_start = datetime.now()

        for task_id in nx.topological_sort(nx_graph):
            predecessors = list(nx_graph.predecessors(task_id))

            if not predecessors:
                start_dates[task_id] = project_start
            else:
                # Start after all predecessors finish
                max_end = project_start
                for pred in predecessors:
                    pred_duration = nx_graph.nodes[pred].get("duration", 8)
                    pred_end = start_dates[pred] + timedelta(hours=pred_duration)
                    if pred_end > max_end:
                        max_end = pred_end
                start_dates[task_id] = max_end

        # Build Gantt data
        gantt_tasks = []
        for task in tasks:
            task_id = str(task.id)
            start = start_dates.get(task_id, project_start)
            duration = task.estimated_hours or 8
            end = start + timedelta(hours=duration)

            # Get dependencies as comma-separated IDs
            deps = list(nx_graph.predecessors(task_id))

            gantt_tasks.append({
                "id": task_id,
                "name": task.title,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "progress": 100 if task.status.value == "completed" else 0,
                "dependencies": ",".join(deps),
                "assignee": task.assignee,
                "type": "task",
            })

        return gantt_tasks
