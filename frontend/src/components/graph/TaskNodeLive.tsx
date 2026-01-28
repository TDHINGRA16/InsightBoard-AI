"use client";

import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    CheckCircle2,
    Clock,
    Loader2,
    Play,
    RotateCcw,
    User,
    AlertTriangle,
} from "lucide-react";
import { TaskPriority, TaskStatus, JobStatus } from "@/types/enums";
import { cn } from "@/lib/utils";

export interface TaskNodeLiveData {
    label: string;
    title: string;
    priority: TaskPriority;
    status: TaskStatus;
    assignee?: string;
    estimated_hours?: number;
    is_critical?: boolean;
    slack?: number;
    job_id?: string;
    job_status?: JobStatus;
    job_progress?: number;
    error_message?: string;
    dependencies_completed?: boolean;
    onComplete?: (taskId: string) => void;
    onStart?: (taskId: string) => void;
    onRetry?: (taskId: string) => void;
    isActionLoading?: boolean;
}

const priorityColors: Record<TaskPriority, string> = {
    [TaskPriority.LOW]: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    [TaskPriority.MEDIUM]: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
    [TaskPriority.HIGH]: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
    [TaskPriority.CRITICAL]: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
};

const statusConfig: Record<TaskStatus, { color: string; bgColor: string; icon: any }> = {
    [TaskStatus.PENDING]: {
        color: "border-slate-300 dark:border-slate-600",
        bgColor: "bg-slate-50 dark:bg-slate-900",
        icon: Clock,
    },
    [TaskStatus.IN_PROGRESS]: {
        color: "border-blue-400 dark:border-blue-500",
        bgColor: "bg-blue-50 dark:bg-blue-950",
        icon: Play,
    },
    [TaskStatus.COMPLETED]: {
        color: "border-emerald-400 dark:border-emerald-500",
        bgColor: "bg-emerald-50 dark:bg-emerald-950",
        icon: CheckCircle2,
    },
    [TaskStatus.BLOCKED]: {
        color: "border-red-400 dark:border-red-500",
        bgColor: "bg-red-50 dark:bg-red-950",
        icon: AlertTriangle,
    },
};

const jobStatusColors: Record<JobStatus, string> = {
    [JobStatus.QUEUED]: "bg-slate-200 text-slate-700",
    [JobStatus.PROCESSING]: "bg-blue-200 text-blue-800",
    [JobStatus.COMPLETED]: "bg-emerald-200 text-emerald-800",
    [JobStatus.FAILED]: "bg-red-200 text-red-800",
};

function TaskNodeLive({ id, data, selected }: NodeProps<TaskNodeLiveData>) {
    const config = statusConfig[data.status];
    const StatusIcon = config.icon;
    const isProcessing = data.job_status === JobStatus.PROCESSING;
    const canComplete = data.status !== TaskStatus.COMPLETED && data.dependencies_completed !== false;
    const canStart = data.status === TaskStatus.PENDING && data.dependencies_completed !== false;
    const hasFailed = data.job_status === JobStatus.FAILED || data.status === TaskStatus.BLOCKED;

    return (
        <>
            <Handle
                type="target"
                position={Position.Top}
                className="!bg-primary !w-3 !h-3 !border-2 !border-background"
            />

            <Card
                className={cn(
                    "min-w-[240px] max-w-[300px] p-4 cursor-pointer transition-all duration-200",
                    "border-2 shadow-md hover:shadow-lg",
                    config.color,
                    config.bgColor,
                    selected && "ring-2 ring-primary ring-offset-2 ring-offset-background",
                    data.is_critical && "border-red-500 shadow-red-200/50 dark:shadow-red-900/30 shadow-lg",
                    isProcessing && "animate-pulse"
                )}
            >
                {/* Critical Path Indicator */}
                {data.is_critical && (
                    <div className="absolute -top-2 -right-2">
                        <span className="flex h-4 w-4">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                            <span className="relative inline-flex rounded-full h-4 w-4 bg-red-500" />
                        </span>
                    </div>
                )}

                {/* Processing Indicator */}
                {isProcessing && (
                    <div className="absolute -top-2 -left-2">
                        <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
                    </div>
                )}

                {/* Status Icon */}
                <div className="flex items-start justify-between mb-2">
                    <StatusIcon
                        className={cn(
                            "h-4 w-4",
                            data.status === TaskStatus.COMPLETED && "text-emerald-500",
                            data.status === TaskStatus.IN_PROGRESS && "text-blue-500",
                            data.status === TaskStatus.BLOCKED && "text-red-500",
                            data.status === TaskStatus.PENDING && "text-slate-400"
                        )}
                    />
                    {data.job_status && (
                        <Badge
                            className={cn("text-[10px] px-1.5 py-0", jobStatusColors[data.job_status])}
                        >
                            {data.job_status}
                        </Badge>
                    )}
                </div>

                {/* Title */}
                <h3 className="font-semibold text-sm line-clamp-2 mb-2">
                    {data.title || data.label}
                </h3>

                {/* Progress Bar (if processing) */}
                {isProcessing && data.job_progress !== undefined && (
                    <div className="mb-2">
                        <div className="flex justify-between text-xs text-muted-foreground mb-1">
                            <span>Progress</span>
                            <span>{data.job_progress}%</span>
                        </div>
                        <div className="h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-blue-500 rounded-full transition-all duration-300"
                                style={{ width: `${data.job_progress}%` }}
                            />
                        </div>
                    </div>
                )}

                {/* Error Message */}
                {hasFailed && data.error_message && (
                    <div className="mb-2 p-2 bg-red-100 dark:bg-red-900/30 rounded text-xs text-red-700 dark:text-red-400 line-clamp-2">
                        {data.error_message}
                    </div>
                )}

                {/* Badges */}
                <div className="flex gap-2 mb-3 flex-wrap">
                    <Badge className={cn("text-xs", priorityColors[data.priority])}>
                        {data.priority}
                    </Badge>
                    <Badge variant="outline" className="text-xs capitalize">
                        {data.status.replace("_", " ")}
                    </Badge>
                </div>

                {/* Meta */}
                <div className="flex flex-wrap gap-3 text-xs text-muted-foreground mb-3">
                    {data.assignee && (
                        <div className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            <span>{data.assignee}</span>
                        </div>
                    )}
                    {data.estimated_hours !== undefined && data.estimated_hours > 0 && (
                        <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>{data.estimated_hours}h</span>
                        </div>
                    )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                    {canStart && data.onStart && (
                        <Button
                            size="sm"
                            variant="outline"
                            className="flex-1 h-7 text-xs"
                            onClick={(e) => {
                                e.stopPropagation();
                                data.onStart?.(id);
                            }}
                            disabled={data.isActionLoading}
                        >
                            {data.isActionLoading ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                                <>
                                    <Play className="h-3 w-3 mr-1" />
                                    Start
                                </>
                            )}
                        </Button>
                    )}
                    {canComplete && data.onComplete && data.status !== TaskStatus.PENDING && (
                        <Button
                            size="sm"
                            variant="default"
                            className="flex-1 h-7 text-xs bg-emerald-600 hover:bg-emerald-700"
                            onClick={(e) => {
                                e.stopPropagation();
                                data.onComplete?.(id);
                            }}
                            disabled={data.isActionLoading}
                        >
                            {data.isActionLoading ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                                <>
                                    <CheckCircle2 className="h-3 w-3 mr-1" />
                                    Complete
                                </>
                            )}
                        </Button>
                    )}
                    {hasFailed && data.onRetry && (
                        <Button
                            size="sm"
                            variant="destructive"
                            className="flex-1 h-7 text-xs"
                            onClick={(e) => {
                                e.stopPropagation();
                                data.onRetry?.(id);
                            }}
                            disabled={data.isActionLoading}
                        >
                            {data.isActionLoading ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                                <>
                                    <RotateCcw className="h-3 w-3 mr-1" />
                                    Retry
                                </>
                            )}
                        </Button>
                    )}
                </div>

                {/* Slack indicator */}
                {data.slack !== undefined && data.slack > 0 && (
                    <div className="mt-2 text-xs text-muted-foreground">
                        Slack: {data.slack.toFixed(1)}h
                    </div>
                )}
            </Card>

            <Handle
                type="source"
                position={Position.Bottom}
                className="!bg-primary !w-3 !h-3 !border-2 !border-background"
            />
        </>
    );
}

export default memo(TaskNodeLive);
