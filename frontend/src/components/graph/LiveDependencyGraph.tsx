"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    Connection,
    Edge,
    Node,
    BackgroundVariant,
    Panel,
} from "reactflow";
import "reactflow/dist/style.css";

import TaskNodeLive, { TaskNodeLiveData } from "./TaskNodeLive";
import { TaskDetailsPanel } from "./TaskDetailsPanel";
import { useGraphPolling } from "@/hooks/useGraphPolling";
import { useTaskActions } from "@/hooks/useTaskActions";
import { useGraphStore } from "@/store";
import { Task, GraphData, GraphNode, GraphEdge } from "@/types";
import { TaskStatus, JobStatus } from "@/types/enums";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    Loader2,
    RefreshCcw,
    Activity,
    CheckCircle2,
    AlertTriangle,
    Clock,
    Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface LiveDependencyGraphProps {
    transcriptId: string;
    onNodeClick?: (nodeId: string) => void;
}

const nodeTypes = {
    taskNode: TaskNodeLive,
};

/**
 * Live dependency graph with real-time status polling and task actions.
 */
export function LiveDependencyGraph({
    transcriptId,
    onNodeClick,
}: LiveDependencyGraphProps) {
    const { highlightCriticalPath, showMiniMap, setSelectedNodeId, selectedNodeId } =
        useGraphStore();

    const [selectedTask, setSelectedTask] = useState<Task | null>(null);
    const [dependencyTitles, setDependencyTitles] = useState<string[]>([]);
    const [dependentTitles, setDependentTitles] = useState<string[]>([]);

    // Polling hook
    const {
        graphData,
        criticalPath,
        tasks,
        activeJobs,
        isLoading,
        error,
        lastUpdated,
        completionPercentage,
        refresh,
    } = useGraphPolling({
        transcriptId,
        enabled: true,
        pollingInterval: 2000,
    });

    // Task actions hook
    const {
        isLoading: isActionLoading,
        loadingTaskId,
        completeTask,
        startTask,
        blockTask,
        resetTask,
    } = useTaskActions({
        onTaskUpdated: () => {
            // Refresh graph after task update
            setTimeout(refresh, 500);
        },
    });

    // Build task map for quick lookup
    const taskMap = useMemo(() => {
        const map = new Map<string, Task>();
        tasks.forEach((task) => map.set(task.id, task));
        return map;
    }, [tasks]);

    // Build job status map
    const jobStatusMap = useMemo(() => {
        const map = new Map<string, { status: JobStatus; progress: number }>();
        activeJobs.forEach((job) => {
            map.set(job.id, { status: job.status, progress: job.progress });
        });
        return map;
    }, [activeJobs]);

    // Check if all dependencies are completed for a task
    const checkDependenciesCompleted = useCallback(
        (task: Task): boolean => {
            if (!task.dependencies || task.dependencies.length === 0) return true;

            // Assuming dependencies is an array of dependency objects or task IDs
            const depTaskIds = task.dependencies.map((d: any) =>
                typeof d === 'string' ? d : d.depends_on_task_id
            );

            return depTaskIds.every((depId: string) => {
                const depTask = taskMap.get(depId);
                return depTask?.status === TaskStatus.COMPLETED;
            });
        },
        [taskMap]
    );

    // Action handlers that include the task title
    const handleCompleteTask = useCallback(
        async (taskId: string) => {
            const task = taskMap.get(taskId);
            await completeTask(taskId, task?.title);
        },
        [completeTask, taskMap]
    );

    const handleStartTask = useCallback(
        async (taskId: string) => {
            const task = taskMap.get(taskId);
            await startTask(taskId, task?.title);
        },
        [startTask, taskMap]
    );

    const handleBlockTask = useCallback(
        async (taskId: string) => {
            const task = taskMap.get(taskId);
            await blockTask(taskId, task?.title);
        },
        [blockTask, taskMap]
    );

    const handleResetTask = useCallback(
        async (taskId: string) => {
            const task = taskMap.get(taskId);
            await resetTask(taskId, task?.title);
        },
        [resetTask, taskMap]
    );

    // Process nodes with live data
    const initialNodes = useMemo(() => {
        if (!graphData?.nodes) return [];

        return graphData.nodes.map((node: GraphNode) => {
            const task = taskMap.get(node.id);
            const isCritical = highlightCriticalPath && criticalPath.includes(node.id);
            const dependenciesCompleted = task ? checkDependenciesCompleted(task) : true;

            const nodeData: TaskNodeLiveData = {
                ...node.data,
                is_critical: isCritical,
                dependencies_completed: dependenciesCompleted,
                onComplete: handleCompleteTask,
                onStart: handleStartTask,
                onRetry: handleStartTask, // Reset to pending to retry
                isActionLoading: loadingTaskId === node.id,
            };

            return {
                ...node,
                type: "taskNode",
                data: nodeData,
            };
        });
    }, [
        graphData?.nodes,
        taskMap,
        criticalPath,
        highlightCriticalPath,
        loadingTaskId,
        checkDependenciesCompleted,
        handleCompleteTask,
        handleStartTask,
    ]);

    // Process edges with critical path styling
    const initialEdges = useMemo(() => {
        if (!graphData?.edges) return [];

        return graphData.edges.map((edge: GraphEdge) => {
            const isCriticalEdge =
                highlightCriticalPath &&
                criticalPath.includes(edge.source) &&
                criticalPath.includes(edge.target);

            // Check if source task is completed
            const sourceTask = taskMap.get(edge.source);
            const isCompleted = sourceTask?.status === TaskStatus.COMPLETED;

            return {
                ...edge,
                type: "smoothstep",
                animated: isCriticalEdge || !isCompleted,
                style: isCriticalEdge
                    ? { stroke: "#ef4444", strokeWidth: 3 }
                    : isCompleted
                        ? { stroke: "#10b981", strokeWidth: 2 }
                        : { stroke: "#94a3b8", strokeWidth: 2 },
            };
        });
    }, [graphData?.edges, criticalPath, highlightCriticalPath, taskMap]);

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    // Update nodes/edges when data changes
    useEffect(() => {
        setNodes(initialNodes);
        setEdges(initialEdges);
    }, [initialNodes, initialEdges, setNodes, setEdges]);

    // Handle node selection
    const handleNodeClick = useCallback(
        (_: any, node: Node) => {
            setSelectedNodeId(node.id);
            onNodeClick?.(node.id);

            const task = taskMap.get(node.id);
            if (task) {
                setSelectedTask(task);

                // Get dependency titles
                if (task.dependencies && Array.isArray(task.dependencies)) {
                    const depIds = task.dependencies.map((d: any) =>
                        typeof d === "string" ? d : d.depends_on_task_id
                    );
                    const titles = depIds
                        .map((id: string) => taskMap.get(id)?.title)
                        .filter(Boolean) as string[];
                    setDependencyTitles(titles);
                } else {
                    setDependencyTitles([]);
                }

                // Get dependent titles
                if (task.dependents && Array.isArray(task.dependents)) {
                    const depIds = task.dependents.map((d: any) =>
                        typeof d === "string" ? d : d.task_id
                    );
                    const titles = depIds
                        .map((id: string) => taskMap.get(id)?.title)
                        .filter(Boolean) as string[];
                    setDependentTitles(titles);
                } else {
                    setDependentTitles([]);
                }
            }
        },
        [setSelectedNodeId, onNodeClick, taskMap]
    );

    // Close details panel
    const handleCloseDetails = useCallback(() => {
        setSelectedTask(null);
        setSelectedNodeId(null);
    }, [setSelectedNodeId]);

    const onConnect = useCallback(
        (params: Connection) => {
            const newEdge: Edge = {
                id: `e${params.source}-${params.target}`,
                source: params.source!,
                target: params.target!,
                type: "smoothstep",
                style: { stroke: "#94a3b8", strokeWidth: 2 },
            };
            setEdges((eds) => [...eds, newEdge]);
        },
        [setEdges]
    );

    // Stats
    const stats = useMemo(() => {
        const completed = tasks.filter((t) => t.status === TaskStatus.COMPLETED).length;
        const inProgress = tasks.filter((t) => t.status === TaskStatus.IN_PROGRESS).length;
        const blocked = tasks.filter((t) => t.status === TaskStatus.BLOCKED).length;
        const pending = tasks.filter((t) => t.status === TaskStatus.PENDING).length;

        return { completed, inProgress, blocked, pending, total: tasks.length };
    }, [tasks]);

    if (isLoading && !graphData) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-muted/30 rounded-lg">
                <div className="text-center space-y-3">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                    <p className="text-sm text-muted-foreground">Loading dependency graph...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-muted/30 rounded-lg">
                <div className="text-center space-y-3">
                    <AlertTriangle className="h-8 w-8 mx-auto text-destructive" />
                    <p className="text-sm text-destructive">{error}</p>
                    <Button variant="outline" size="sm" onClick={refresh}>
                        <RefreshCcw className="h-4 w-4 mr-2" />
                        Retry
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full h-full flex">
            {/* Main Graph */}
            <div className="flex-1 bg-muted/30 rounded-lg relative">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    onNodeClick={handleNodeClick}
                    nodeTypes={nodeTypes}
                    fitView
                    fitViewOptions={{ padding: 0.2 }}
                    minZoom={0.1}
                    maxZoom={2}
                    defaultEdgeOptions={{
                        type: "smoothstep",
                    }}
                >
                    <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
                    <Controls />

                    {showMiniMap && (
                        <MiniMap
                            nodeStrokeWidth={3}
                            nodeColor={(node) => {
                                const data = node.data as TaskNodeLiveData;
                                if (data?.is_critical) return "#ef4444";
                                if (data?.status === TaskStatus.COMPLETED) return "#10b981";
                                if (data?.status === TaskStatus.IN_PROGRESS) return "#3b82f6";
                                if (data?.status === TaskStatus.BLOCKED) return "#ef4444";
                                return "#94a3b8";
                            }}
                            maskColor="rgb(0, 0, 0, 0.1)"
                        />
                    )}

                    {/* Stats Panel */}
                    <Panel position="top-left" className="space-y-2">
                        <Card className="p-3">
                            <div className="flex items-center gap-4 text-sm">
                                <div className="flex items-center gap-1.5">
                                    <Activity className="h-4 w-4 text-primary" />
                                    <span className="font-medium">
                                        {completionPercentage}% Complete
                                    </span>
                                </div>
                                <div className="h-4 w-px bg-border" />
                                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                    <span className="flex items-center gap-1">
                                        <div className="h-2 w-2 rounded-full bg-emerald-500" />
                                        {stats.completed}
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <div className="h-2 w-2 rounded-full bg-blue-500" />
                                        {stats.inProgress}
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <div className="h-2 w-2 rounded-full bg-slate-400" />
                                        {stats.pending}
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <div className="h-2 w-2 rounded-full bg-red-500" />
                                        {stats.blocked}
                                    </span>
                                </div>
                            </div>
                        </Card>
                    </Panel>

                    {/* Polling Status */}
                    <Panel position="top-right">
                        <div className="flex items-center gap-2">
                            {activeJobs.length > 0 && (
                                <Badge
                                    variant="secondary"
                                    className="bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                                >
                                    <Zap className="h-3 w-3 mr-1 animate-pulse" />
                                    {activeJobs.length} Active Job{activeJobs.length > 1 ? "s" : ""}
                                </Badge>
                            )}
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={refresh}
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <RefreshCcw className="h-4 w-4" />
                                )}
                            </Button>
                        </div>
                    </Panel>

                    {/* Critical Path Legend */}
                    {highlightCriticalPath && criticalPath.length > 0 && (
                        <Panel position="bottom-left">
                            <Card className="p-2 text-xs">
                                <div className="flex items-center gap-2">
                                    <div className="h-3 w-6 bg-red-500 rounded" />
                                    <span>Critical Path ({criticalPath.length} tasks)</span>
                                </div>
                            </Card>
                        </Panel>
                    )}
                </ReactFlow>
            </div>

            {/* Details Panel */}
            {selectedTask && (
                <div className="w-80 flex-shrink-0 ml-4">
                    <TaskDetailsPanel
                        task={selectedTask}
                        dependencyTitles={dependencyTitles}
                        dependentTitles={dependentTitles}
                        onClose={handleCloseDetails}
                        onComplete={handleCompleteTask}
                        onStart={handleStartTask}
                        onBlock={handleBlockTask}
                        onReset={handleResetTask}
                        isLoading={isActionLoading}
                    />
                </div>
            )}
        </div>
    );
}
