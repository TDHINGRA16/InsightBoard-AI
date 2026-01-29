"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Clock,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileText,
  Upload,
  Search,
  AlertTriangle
} from "lucide-react";

import { api } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard-analytics"],
    queryFn: async () => {
      const res = await api.getDashboardAnalytics();
      return res.data?.data;
    },
  });

  if (isLoading) return <Loading text="Loading dashboard..." />;

  const stats = data ?? {};
  const tasksByStatus = stats.tasks?.by_status ?? {};
  const tasksByPriority = stats.tasks?.by_priority ?? {};
  const transcriptsByStatus = stats.transcripts?.by_status ?? {};
  const jobsByStatus = stats.jobs?.by_status ?? {};
  const totalTasks = stats.total_tasks ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Workspace overview & analytics."
        actions={
          <Button asChild>
            <Link href="/transcripts">Add Transcript</Link>
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Total Transcripts" value={stats.total_transcripts ?? 0} />
        <StatCard title="Total Tasks" value={stats.total_tasks ?? 0} />
        <StatCard title="Completed Tasks" value={stats.completed_tasks ?? 0} />
        <StatCard title="Pending Tasks" value={stats.pending_tasks ?? 0} />
      </div>

      {/* Detailed Analytics */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Tasks by Status */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">Tasks by Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <StatusRow
              icon={<Clock className="h-4 w-4 text-amber-500" />}
              label="Pending"
              count={tasksByStatus.pending ?? 0}
            />
            <StatusRow
              icon={<Loader2 className="h-4 w-4 text-blue-500" />}
              label="In Progress"
              count={tasksByStatus.in_progress ?? 0}
            />
            <StatusRow
              icon={<CheckCircle2 className="h-4 w-4 text-green-500" />}
              label="Completed"
              count={tasksByStatus.completed ?? 0}
            />
            <StatusRow
              icon={<XCircle className="h-4 w-4 text-red-500" />}
              label="Blocked"
              count={tasksByStatus.blocked ?? 0}
            />
          </CardContent>
        </Card>

        {/* Tasks by Priority */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">Tasks by Priority</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <PriorityRow
              label="Critical"
              count={tasksByPriority.critical ?? 0}
              total={totalTasks}
              color="bg-red-500"
            />
            <PriorityRow
              label="High"
              count={tasksByPriority.high ?? 0}
              total={totalTasks}
              color="bg-orange-500"
            />
            <PriorityRow
              label="Medium"
              count={tasksByPriority.medium ?? 0}
              total={totalTasks}
              color="bg-yellow-500"
            />
            <PriorityRow
              label="Low"
              count={tasksByPriority.low ?? 0}
              total={totalTasks}
              color="bg-gray-400"
            />
          </CardContent>
        </Card>

        {/* Transcripts by Status */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">Transcripts by Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <StatusRow
              icon={<Upload className="h-4 w-4 text-slate-500" />}
              label="Uploaded"
              count={transcriptsByStatus.uploaded ?? 0}
            />
            <StatusRow
              icon={<Loader2 className="h-4 w-4 text-blue-500" />}
              label="Analyzing"
              count={transcriptsByStatus.analyzing ?? 0}
            />
            <StatusRow
              icon={<CheckCircle2 className="h-4 w-4 text-green-500" />}
              label="Analyzed"
              count={transcriptsByStatus.analyzed ?? 0}
            />
            <StatusRow
              icon={<AlertTriangle className="h-4 w-4 text-red-500" />}
              label="Failed"
              count={transcriptsByStatus.failed ?? 0}
            />
          </CardContent>
        </Card>

        {/* Jobs Overview */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">Jobs Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <StatusRow
              icon={<Clock className="h-4 w-4 text-slate-500" />}
              label="Queued"
              count={jobsByStatus.queued ?? 0}
            />
            <StatusRow
              icon={<Loader2 className="h-4 w-4 text-blue-500" />}
              label="Processing"
              count={jobsByStatus.processing ?? 0}
            />
            <StatusRow
              icon={<CheckCircle2 className="h-4 w-4 text-green-500" />}
              label="Completed"
              count={jobsByStatus.completed ?? 0}
            />
            <StatusRow
              icon={<XCircle className="h-4 w-4 text-red-500" />}
              label="Failed"
              count={jobsByStatus.failed ?? 0}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: number }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-muted-foreground font-normal">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold">{value}</div>
      </CardContent>
    </Card>
  );
}

function StatusRow({
  icon,
  label,
  count
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <span className="text-sm font-medium">{count}</span>
    </div>
  );
}

function PriorityRow({
  label,
  count,
  total,
  color
}: {
  label: string;
  count: number;
  total: number;
  color: string;
}) {
  const percentage = total > 0 ? (count / total) * 100 : 0;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span>{label}</span>
        <span className="font-medium">{count}</span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

