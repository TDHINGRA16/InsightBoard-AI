"use client";

import { useMemo, useCallback, useEffect, useRef } from "react";
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    Node,
    BackgroundVariant,
} from "reactflow";
import "reactflow/dist/style.css";

import TaskNode from "./TaskNode";
import { useGraphStore } from "@/store";
import { GraphData } from "@/types";

interface DependencyGraphProps {
    graphData: GraphData;
    criticalPath?: string[];
    onNodeClick?: (nodeId: string) => void;
    onCompleteTask?: (nodeId: string) => void;
}

const nodeTypes = {
    taskNode: TaskNode,
};

export function DependencyGraph({
    graphData,
    criticalPath = [],
    onNodeClick,
    onCompleteTask,
}: DependencyGraphProps) {
    const { highlightCriticalPath, showMiniMap, setSelectedNodeId, layoutDirection } =
        useGraphStore();

    // Track previous layout direction to detect changes
    const prevLayoutRef = useRef(layoutDirection);

    // Helper function to transform position based on layout direction
    const transformPosition = useCallback((position: { x: number; y: number }, direction: "TB" | "LR") => {
        if (direction === "LR") {
            return { x: position.y, y: position.x };
        }
        return position;
    }, []);

    // Process nodes with critical path highlighting, complete callback, and layout transformation
    const initialNodes = useMemo(() => {
        return graphData.nodes.map((node) => {
            const position = transformPosition(node.position, layoutDirection);

            return {
                ...node,
                position,
                type: "taskNode",
                data: {
                    ...node.data,
                    is_critical:
                        highlightCriticalPath && criticalPath.includes(node.id),
                    onComplete: onCompleteTask,
                },
            };
        });
    }, [graphData.nodes, criticalPath, highlightCriticalPath, onCompleteTask, layoutDirection, transformPosition]);

    // Process edges with critical path styling
    const initialEdges = useMemo(() => {
        return graphData.edges.map((edge) => {
            const isCriticalEdge =
                highlightCriticalPath &&
                criticalPath.includes(edge.source) &&
                criticalPath.includes(edge.target);

            return {
                ...edge,
                animated: isCriticalEdge,
                style: isCriticalEdge
                    ? { stroke: "#ef4444", strokeWidth: 3 }
                    : { stroke: "#94a3b8", strokeWidth: 2 },
            };
        });
    }, [graphData.edges, criticalPath, highlightCriticalPath]);

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    // Update nodes when graphData changes
    // If layout direction changed, use new positions; otherwise preserve user-moved positions
    useEffect(() => {
        const layoutChanged = prevLayoutRef.current !== layoutDirection;
        prevLayoutRef.current = layoutDirection;

        if (layoutChanged) {
            // Layout direction changed - use new calculated positions (don't preserve old positions)
            setNodes(initialNodes);
        } else {
            // Normal update - preserve user-moved positions
            setNodes((currentNodes) => {
                const positionMap = new Map<string, { x: number; y: number }>();
                currentNodes.forEach((node) => {
                    positionMap.set(node.id, node.position);
                });

                return initialNodes.map((node) => ({
                    ...node,
                    position: positionMap.get(node.id) ?? node.position,
                }));
            });
        }
    }, [initialNodes, setNodes, layoutDirection]);

    // Update edges when graphData changes
    useEffect(() => {
        setEdges(initialEdges);
    }, [initialEdges, setEdges]);

    const handleNodeClick = useCallback(
        (_: any, node: Node) => {
            setSelectedNodeId(node.id);
            onNodeClick?.(node.id);
        },
        [setSelectedNodeId, onNodeClick]
    );

    return (
        <div className="w-full h-full bg-muted/30 rounded-lg">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={handleNodeClick}
                nodeTypes={nodeTypes}
                // Disable connections and edge editing
                nodesConnectable={false}
                edgesUpdatable={false}
                connectOnClick={false}
                // View settings
                fitView
                fitViewOptions={{ padding: 0.3, maxZoom: 0.9 }}
                minZoom={0.1}
                maxZoom={1.5}
                defaultViewport={{ x: 0, y: 0, zoom: 0.7 }}
                defaultEdgeOptions={{
                    type: "smoothstep",
                }}
            >
                <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
                <Controls showZoom showFitView showInteractive={false} />
                {showMiniMap && (
                    <MiniMap
                        nodeStrokeWidth={3}
                        nodeColor={(node) => {
                            if (node.data?.status === "completed") return "#22c55e";
                            if (node.data?.is_critical) return "#ef4444";
                            return "#3b82f6";
                        }}
                        maskColor="rgb(0, 0, 0, 0.1)"
                        position="bottom-right"
                    />
                )}
            </ReactFlow>
        </div>
    );
}
