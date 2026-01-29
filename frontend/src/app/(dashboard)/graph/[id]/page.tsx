"use client";

import { useMemo, useCallback, useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { api, apiClient } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { DependencyGraph } from "@/components/graph";
import { useGraphStore } from "@/store";
import { TaskStatus } from "@/types";
import { toast } from "@/lib/toast";
import { RefreshCw, ArrowRightLeft, ArrowUpDown } from "lucide-react";

export default function GraphPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { layoutDirection, setLayoutDirection } = useGraphStore();

  // Fetch fresh graph data (disable cache for real-time updates)
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["graph", id],
    queryFn: async () => {
      // Use use_cache=false to get fresh task statuses
      const res = await apiClient.get(`/graphs/${id}?use_cache=false`);
      return res.data?.data;
    },
    staleTime: 0, // Always refetch on mount
    refetchOnWindowFocus: true,
  });

  const { data: criticalPath, refetch: refetchCriticalPath } = useQuery({
    queryKey: ["critical-path", id],
    queryFn: async () => {
      const res = await api.getCriticalPath(id);
      return res.data?.critical_path ?? [];
    },
    enabled: !!data,
  });

  // Mutation to complete a task
  const completeTaskMutation = useMutation({
    mutationFn: async (taskId: string) => {
      const res = await apiClient.post(`/tasks/${taskId}/complete`);
      return res.data;
    },
    onSuccess: (response, taskId) => {
      if (response?.success === false) {
        // Task is blocked
        toast.error(response?.message || "Task is blocked by dependencies");
        return;
      }

      toast.success("Task completed! Dependent tasks unlocked.");

      // Invalidate and refetch graph + critical path to update UI
      queryClient.invalidateQueries({ queryKey: ["graph", id] });
      queryClient.invalidateQueries({ queryKey: ["critical-path", id] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });

      // Force immediate refetch
      refetch();
      refetchCriticalPath();
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || "Failed to complete task");
    },
  });

  // Manual refresh button handler
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([refetch(), refetchCriticalPath()]);
      toast.success("Graph refreshed");
    } finally {
      setIsRefreshing(false);
    }
  };

  // Process graph data with blocking logic
  const graphData = useMemo(() => {
    if (!data) return { nodes: [], edges: [], incoming: new Map(), completed: new Set() };

    const nodes = data.nodes ?? [];
    const edges = data.edges ?? [];

    const completed = new Set(
      nodes
        .filter((n: any) => n?.data?.status === TaskStatus.COMPLETED)
        .map((n: any) => n.id)
    );

    // Build incoming edge map: target -> [source]
    const incoming = new Map<string, string[]>();
    edges.forEach((e: any) => {
      if (!incoming.has(e.target)) incoming.set(e.target, []);
      incoming.get(e.target)!.push(e.source);
    });

    const blocked = new Set<string>();
    nodes.forEach((n: any) => {
      if (completed.has(n.id)) return;
      const prereqs = incoming.get(n.id) ?? [];
      const unmet = prereqs.find((src: string) => !completed.has(src));
      if (unmet) blocked.add(n.id);
    });

    const nodesWithBlocking = nodes.map((n: any) => ({
      ...n,
      data: {
        ...n.data,
        is_blocked: blocked.has(n.id),
      },
    }));

    return { nodes: nodesWithBlocking, edges, incoming, completed };
  }, [data]);

  // Handle completing a task from the graph node
  const handleCompleteTask = useCallback(
    (nodeId: string) => {
      const node = graphData.nodes.find((n: any) => n.id === nodeId);
      if (node?.data?.is_blocked) {
        // Find the blocking dependency
        const prereqs = graphData.incoming.get(nodeId) ?? [];
        const unmet = prereqs.find((src: string) => !graphData.completed.has(src));
        const unmetTitle =
          graphData.nodes.find((n: any) => n.id === unmet)?.data?.title ?? unmet ?? "a dependency";
        toast.error(`Task is blocked. Complete "${unmetTitle}" first.`);
        return;
      }
      completeTaskMutation.mutate(nodeId);
    },
    [graphData, completeTaskMutation]
  );

  const onNodeClick = useCallback(
    (nodeId: string) => {
      const node = graphData.nodes.find((n: any) => n.id === nodeId);
      if (node?.data?.is_blocked) {
        // Try to find the first unmet dependency title
        const prereqs = graphData.incoming.get(nodeId) ?? [];
        const unmet = prereqs.find((src: string) => !graphData.completed.has(src));
        const unmetTitle =
          graphData.nodes.find((n: any) => n.id === unmet)?.data?.title ?? unmet ?? "a dependency";
        toast.error(`Task is blocked. Complete "${unmetTitle}" first.`);
        return;
      }
      router.push(`/tasks/${nodeId}`);
    },
    [graphData, router]
  );

  if (isLoading) return <Loading text="Loading graph..." />;
  if (!data) return <div>Graph not found</div>;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Dependency Graph"
        description="Visualize tasks and dependencies. Click a node to view details, or click 'Mark Complete' to finish a task."
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setLayoutDirection(layoutDirection === "TB" ? "LR" : "TB")}
              title={layoutDirection === "TB" ? "Switch to horizontal layout" : "Switch to vertical layout"}
            >
              {layoutDirection === "TB" ? (
                <><ArrowRightLeft className="h-4 w-4 mr-2" />Horizontal</>
              ) : (
                <><ArrowUpDown className="h-4 w-4 mr-2" />Vertical</>
              )}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Link href={`/transcripts/${id}`}>
              <Button variant="outline" size="sm">Back to transcript</Button>
            </Link>
          </div>
        }
      />

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 px-2 py-2 bg-muted/50 rounded-lg text-xs">
        <span className="font-medium text-muted-foreground">Legend:</span>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-green-500" />
          <span>Completed</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-blue-500" />
          <span>In Progress</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-amber-500" />
          <span>Pending</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-gray-400" />
          <span>Blocked</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded border-2 border-red-500 bg-red-100" />
          <span>Critical Path</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-6 h-0.5 bg-red-500" />
          <span className="text-red-600">Critical Edge</span>
        </div>
      </div>

      {/* Graph Container - Reduced height */}
      <div className="rounded-lg border overflow-hidden" style={{ height: "calc(100vh - 280px)", minHeight: "400px" }}>
        <DependencyGraph
          graphData={{ nodes: graphData.nodes, edges: graphData.edges }}
          criticalPath={criticalPath ?? []}
          onNodeClick={onNodeClick}
          onCompleteTask={handleCompleteTask}
        />
      </div>
    </div>
  );
}

