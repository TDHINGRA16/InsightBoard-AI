"use client";

import { useMemo, useCallback } from "react";
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
} from "reactflow";
import "reactflow/dist/style.css";

import TaskNode from "./TaskNode";
import { useGraphStore } from "@/store";
import { GraphData } from "@/types";

interface DependencyGraphProps {
    graphData: GraphData;
    criticalPath?: string[];
    onNodeClick?: (nodeId: string) => void;
}

const nodeTypes = {
    taskNode: TaskNode,
};

export function DependencyGraph({
    graphData,
    criticalPath = [],
    onNodeClick,
}: DependencyGraphProps) {
    const { highlightCriticalPath, showMiniMap, setSelectedNodeId } =
        useGraphStore();

    // Process nodes with critical path highlighting
    const initialNodes = useMemo(() => {
        return graphData.nodes.map((node) => ({
            ...node,
            type: "taskNode",
            data: {
                ...node.data,
                is_critical:
                    highlightCriticalPath && criticalPath.includes(node.id),
            },
        }));
    }, [graphData.nodes, criticalPath, highlightCriticalPath]);

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

    const onConnect = useCallback(
        (params: Connection) => {
            const newEdge: Edge = {
                id: `e${params.source}-${params.target}`,
                source: params.source!,
                target: params.target!,
                style: { stroke: "#94a3b8", strokeWidth: 2 },
            };
            setEdges((eds) => [...eds, newEdge]);
        },
        [setEdges]
    );

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
                            if (node.data?.is_critical) return "#ef4444";
                            return "#3b82f6";
                        }}
                        maskColor="rgb(0, 0, 0, 0.1)"
                    />
                )}
            </ReactFlow>
        </div>
    );
}
