"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, FileText, CheckCircle2, Clock, AlertCircle } from "lucide-react";

import { api } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Task {
  id: string;
  title: string;
  status: string;
  priority: string;
  transcript_id: string;
  dependencies_count?: number;
  dependents_count?: number;
}

interface Transcript {
  id: string;
  filename: string;
  status: string;
}

export default function TasksPage() {
  const [expandedTranscripts, setExpandedTranscripts] = useState<Set<string>>(new Set());

  // Fetch all transcripts
  const { data: transcriptsData, isLoading: loadingTranscripts } = useQuery({
    queryKey: ["transcripts"],
    queryFn: async () => {
      const res = await api.getTranscripts({ page: 1, page_size: 50 });
      return res.data;
    },
  });

  // Fetch all tasks
  const { data: tasksData, isLoading: loadingTasks, refetch } = useQuery({
    queryKey: ["tasks"],
    queryFn: async () => {
      const res = await api.getTasks({ page: 1, page_size: 100 });
      return res.data;
    },
  });

  const transcripts = useMemo(() => transcriptsData?.data ?? [], [transcriptsData]);
  const allTasks = useMemo(() => tasksData?.data ?? [], [tasksData]);

  // Group tasks by transcript
  const tasksByTranscript = useMemo(() => {
    const grouped = new Map<string, Task[]>();
    allTasks.forEach((task: Task) => {
      const transcriptId = task.transcript_id;
      if (!grouped.has(transcriptId)) {
        grouped.set(transcriptId, []);
      }
      grouped.get(transcriptId)!.push(task);
    });
    return grouped;
  }, [allTasks]);

  // Filter transcripts that have tasks
  const transcriptsWithTasks = useMemo(() => {
    return transcripts.filter((t: Transcript) => tasksByTranscript.has(t.id));
  }, [transcripts, tasksByTranscript]);

  const toggleTranscript = (id: string) => {
    setExpandedTranscripts((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const getTaskStats = (transcriptId: string) => {
    const tasks = tasksByTranscript.get(transcriptId) ?? [];
    const completed = tasks.filter((t) => t.status === "completed").length;
    const pending = tasks.filter((t) => t.status === "pending").length;
    const inProgress = tasks.filter((t) => t.status === "in_progress").length;
    return { total: tasks.length, completed, pending, inProgress };
  };

  const isLoading = loadingTranscripts || loadingTasks;
  if (isLoading) return <Loading text="Loading tasks..." />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tasks"
        description="Tasks grouped by transcript. Click a transcript to view its tasks."
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Refresh
          </Button>
        }
      />

      {transcriptsWithTasks.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">No transcripts with tasks found.</p>
            <p className="text-sm text-muted-foreground mt-1">
              Upload a transcript and analyze it to extract tasks.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {transcriptsWithTasks.map((transcript: Transcript) => {
            const isExpanded = expandedTranscripts.has(transcript.id);
            const tasks = tasksByTranscript.get(transcript.id) ?? [];
            const stats = getTaskStats(transcript.id);

            return (
              <Card key={transcript.id} className="overflow-hidden">
                {/* Transcript Header - Clickable */}
                <button
                  onClick={() => toggleTranscript(transcript.id)}
                  className="w-full text-left"
                >
                  <CardHeader className="pb-3 hover:bg-muted/50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        )}
                        <FileText className="h-4 w-4 text-primary" />
                        <CardTitle className="text-base font-medium">
                          {transcript.filename || "Untitled Transcript"}
                        </CardTitle>
                      </div>

                      {/* Task Stats */}
                      <div className="flex items-center gap-3 text-sm">
                        <div className="flex items-center gap-1 text-green-600">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          <span>{stats.completed}</span>
                        </div>
                        <div className="flex items-center gap-1 text-amber-600">
                          <Clock className="h-3.5 w-3.5" />
                          <span>{stats.pending + stats.inProgress}</span>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {stats.total} tasks
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                </button>

                {/* Tasks List - Expandable */}
                {isExpanded && (
                  <CardContent className="pt-0 border-t bg-muted/20">
                    <div className="grid gap-3 py-3 md:grid-cols-2 xl:grid-cols-3">
                      {tasks.map((task: Task) => (
                        <div
                          key={task.id}
                          className="bg-background rounded-lg border p-4 space-y-3"
                        >
                          <h4 className="font-medium text-sm line-clamp-2">
                            {task.title}
                          </h4>
                          <div className="flex items-center justify-between">
                            <Badge
                              variant="secondary"
                              className={cn(
                                "text-xs",
                                task.status === "completed" && "bg-green-100 text-green-800",
                                task.status === "in_progress" && "bg-blue-100 text-blue-800",
                                task.status === "pending" && "bg-amber-100 text-amber-800"
                              )}
                            >
                              {task.status.replace("_", " ")}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              deps: {task.dependencies_count ?? 0} • dependents: {task.dependents_count ?? 0}
                            </span>
                          </div>
                          <Link href={`/tasks/${task.id}`}>
                            <Button size="sm" variant="outline" className="w-full text-xs h-7">
                              View Details
                            </Button>
                          </Link>
                        </div>
                      ))}
                    </div>

                    {/* View Graph Link */}
                    <div className="pt-2 border-t flex gap-2">
                      <Link href={`/graph/${transcript.id}`}>
                        <Button size="sm" variant="ghost" className="text-xs">
                          View Dependency Graph
                        </Button>
                      </Link>
                      <Link href={`/transcripts/${transcript.id}`}>
                        <Button size="sm" variant="ghost" className="text-xs">
                          View Transcript
                        </Button>
                      </Link>
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}


