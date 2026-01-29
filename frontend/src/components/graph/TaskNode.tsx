"use client";

import { memo, useCallback, MouseEvent } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Clock, User, CheckCircle2, Check } from "lucide-react";
import { TaskPriority, TaskStatus } from "@/types";
import { cn } from "@/lib/utils";

interface TaskNodeData {
    label: string;
    title: string;
    priority: TaskPriority;
    status: TaskStatus;
    assignee?: string;
    estimated_hours?: number;
    is_critical?: boolean;
    slack?: number;
    is_blocked?: boolean;
    onComplete?: (nodeId: string) => void;
    nodeId?: string;
}

const priorityColors: Record<TaskPriority, string> = {
    [TaskPriority.LOW]: "bg-gray-100 text-gray-800",
    [TaskPriority.MEDIUM]: "bg-yellow-100 text-yellow-800",
    [TaskPriority.HIGH]: "bg-orange-100 text-orange-800",
    [TaskPriority.CRITICAL]: "bg-red-100 text-red-800",
};

const statusColors: Record<TaskStatus, string> = {
    [TaskStatus.PENDING]: "border-slate-300",
    [TaskStatus.IN_PROGRESS]: "border-blue-400",
    [TaskStatus.COMPLETED]: "border-green-500 bg-green-50",
    [TaskStatus.BLOCKED]: "border-red-400",
};

function TaskNode({ data, selected, id }: NodeProps<TaskNodeData>) {
    const isCompleted = data.status === TaskStatus.COMPLETED;
    const canComplete = !isCompleted && !data.is_blocked;

    const handleComplete = useCallback(
        (e: MouseEvent) => {
            e.stopPropagation(); // Prevent node click navigation
            if (data.onComplete && id) {
                data.onComplete(id);
            }
        },
        [data.onComplete, id]
    );

    return (
        <>
            <Handle
                type="target"
                position={Position.Top}
                className="!bg-primary !w-3 !h-3"
            />

            <Card
                className={cn(
                    "min-w-[220px] max-w-[280px] p-4 cursor-pointer transition-all",
                    "border-2",
                    statusColors[data.status],
                    data.is_blocked && "opacity-60 grayscale cursor-not-allowed",
                    selected && "ring-2 ring-primary ring-offset-2",
                    data.is_critical && !isCompleted && "border-red-500 shadow-red-100 shadow-lg"
                )}
            >
                {/* Completed Indicator */}
                {isCompleted && (
                    <div className="absolute -top-2 -left-2">
                        <CheckCircle2 className="h-5 w-5 text-green-500 fill-green-100" />
                    </div>
                )}

                {/* Blocked Indicator */}
                {data.is_blocked && !isCompleted && (
                    <div className="absolute -top-2 -left-2 text-sm" title="Blocked">
                        🔒
                    </div>
                )}

                {/* Critical Path Indicator */}
                {data.is_critical && !isCompleted && (
                    <div className="absolute -top-2 -right-2">
                        <span className="flex h-4 w-4">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                            <span className="relative inline-flex rounded-full h-4 w-4 bg-red-500" />
                        </span>
                    </div>
                )}

                {/* Title */}
                <h3
                    className={cn(
                        "font-semibold text-sm line-clamp-2 mb-2",
                        isCompleted && "line-through text-muted-foreground"
                    )}
                >
                    {data.title || data.label}
                </h3>

                {/* Badges */}
                <div className="flex gap-2 mb-2">
                    <Badge className={cn("text-xs", priorityColors[data.priority])}>
                        {data.priority}
                    </Badge>
                    <Badge
                        variant="outline"
                        className={cn("text-xs", isCompleted && "bg-green-100 text-green-800 border-green-300")}
                    >
                        {data.status.replace("_", " ")}
                    </Badge>
                </div>

                {/* Meta */}
                <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                    {data.assignee && (
                        <div className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            <span>{data.assignee}</span>
                        </div>
                    )}
                    {data.estimated_hours && (
                        <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>{data.estimated_hours}h</span>
                        </div>
                    )}
                </div>

                {/* Slack indicator */}
                {data.slack !== undefined && data.slack > 0 && (
                    <div className="mt-2 text-xs text-muted-foreground">
                        Slack: {data.slack.toFixed(1)}h
                    </div>
                )}

                {/* Complete Button */}
                {canComplete && data.onComplete && (
                    <Button
                        size="sm"
                        variant="outline"
                        className="mt-3 w-full h-7 text-xs bg-green-50 hover:bg-green-100 border-green-300 text-green-700"
                        onClick={handleComplete}
                    >
                        <Check className="h-3 w-3 mr-1" />
                        Mark Complete
                    </Button>
                )}
            </Card>

            <Handle
                type="source"
                position={Position.Bottom}
                className="!bg-primary !w-3 !h-3"
            />
        </>
    );
}

export default memo(TaskNode);
