"use client";

import { useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api, apiClient } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "@/lib/toast";

export default function TaskDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [completing, setCompleting] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["task", id],
    queryFn: async () => {
      const res = await api.getTask(id);
      return res.data?.data;
    },
  });

  const { data: relatedData } = useQuery({
    queryKey: ["task-related", id],
    queryFn: async () => {
      const res = await apiClient.get(`/tasks/${id}/related`);
      return res.data?.data ?? [];
    },
    enabled: !!data,
  });

  const task = data;
  const related = useMemo(() => relatedData ?? [], [relatedData]);

  const complete = async () => {
    setCompleting(true);
    try {
      const res = await apiClient.post(`/tasks/${id}/complete`);
      if (res.data?.success === false) {
        toast.error(res.data?.message || "Task is blocked");
        return;
      }
      toast.success("Task completed! Dependent tasks unlocked.");

      // Invalidate related queries so graph shows updated status
      queryClient.invalidateQueries({ queryKey: ["graph"] });
      queryClient.invalidateQueries({ queryKey: ["critical-path"] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["task-related", id] });

      refetch();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Failed to complete task");
    } finally {
      setCompleting(false);
    }
  };

  if (isLoading) return <Loading text="Loading task..." />;
  if (!task) return <div>Task not found</div>;

  return (
    <div className="space-y-6">
      <PageHeader
        title={task.title}
        description="Task details, dependencies, and actions."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/tasks")}>
              Back
            </Button>
            <Button onClick={complete} disabled={completing || task.status === "completed"}>
              {task.status === "completed" ? "Completed" : completing ? "Completing..." : "Mark complete"}
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">
              {task.description || "No description"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Metadata</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Status</div>
              <Badge variant="secondary">{task.status}</Badge>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Priority</div>
              <div className="text-sm font-medium">{task.priority}</div>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Assignee</div>
              <div className="text-sm font-medium">{task.assignee || "Unassigned"}</div>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Estimated</div>
              <div className="text-sm font-medium">{task.estimated_hours ?? 0}h</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Dependencies</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(task.dependencies ?? []).length === 0 ? (
              <div className="text-sm text-muted-foreground">No dependencies</div>
            ) : (
              (task.dependencies ?? []).map((depId: string) => {
                const dep = related.find((r: any) => r.id === depId);
                return (
                  <div key={depId} className="flex items-center justify-between">
                    <div className="text-sm">{dep?.title ?? depId}</div>
                    <Badge variant="secondary">{dep?.status ?? "unknown"}</Badge>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Dependents</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(task.dependents ?? []).length === 0 ? (
              <div className="text-sm text-muted-foreground">No dependents</div>
            ) : (
              (task.dependents ?? []).map((depId: string) => {
                const dep = related.find((r: any) => r.id === depId);
                return (
                  <div key={depId} className="flex items-center justify-between">
                    <div className="text-sm">{dep?.title ?? depId}</div>
                    <Badge variant="secondary">{dep?.status ?? "unknown"}</Badge>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

