"use client";

import { Task } from "@/types";
import { TaskStatus, TaskPriority } from "@/types/enums";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
    CheckCircle2,
    Clock,
    Loader2,
    Play,
    User,
    Calendar,
    AlertTriangle,
    ArrowRight,
    X,
    RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { format } from "date-fns";

interface TaskDetailsPanelProps {
    task: Task | null;
    dependencyTitles?: string[];
    dependentTitles?: string[];
    onClose: () => void;
    onComplete?: (taskId: string) => void;
    onStart?: (taskId: string) => void;
    onBlock?: (taskId: string) => void;
    onReset?: (taskId: string) => void;
    isLoading?: boolean;
}

const priorityColors: Record<TaskPriority, string> = {
    [TaskPriority.LOW]: "bg-slate-100 text-slate-700",
    [TaskPriority.MEDIUM]: "bg-amber-100 text-amber-800",
    [TaskPriority.HIGH]: "bg-orange-100 text-orange-800",
    [TaskPriority.CRITICAL]: "bg-red-100 text-red-800",
};

const statusConfig: Record<TaskStatus, { color: string; icon: any; label: string }> = {
    [TaskStatus.PENDING]: {
        color: "text-slate-500",
        icon: Clock,
        label: "Pending",
    },
    [TaskStatus.IN_PROGRESS]: {
        color: "text-blue-500",
        icon: Play,
        label: "In Progress",
    },
    [TaskStatus.COMPLETED]: {
        color: "text-emerald-500",
        icon: CheckCircle2,
        label: "Completed",
    },
    [TaskStatus.BLOCKED]: {
        color: "text-red-500",
        icon: AlertTriangle,
        label: "Blocked",
    },
};

export function TaskDetailsPanel({
    task,
    dependencyTitles = [],
    dependentTitles = [],
    onClose,
    onComplete,
    onStart,
    onBlock,
    onReset,
    isLoading = false,
}: TaskDetailsPanelProps) {
    if (!task) {
        return (
            <Card className="w-80 h-full">
                <CardContent className="flex items-center justify-center h-full text-muted-foreground">
                    <p>Select a task to view details</p>
                </CardContent>
            </Card>
        );
    }

    const config = statusConfig[task.status];
    const StatusIcon = config.icon;
    const canComplete = task.status !== TaskStatus.COMPLETED;
    const canStart = task.status === TaskStatus.PENDING;

    return (
        <Card className="w-80 h-full overflow-hidden flex flex-col">
            <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-start justify-between">
                    <CardTitle className="text-lg line-clamp-2 pr-2">{task.title}</CardTitle>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 -mr-2 -mt-1"
                        onClick={onClose}
                    >
                        <X className="h-4 w-4" />
                    </Button>
                </div>
            </CardHeader>

            <CardContent className="flex-1 overflow-auto space-y-4">
                {/* Status */}
                <div className="flex items-center gap-3">
                    <StatusIcon className={cn("h-5 w-5", config.color)} />
                    <div>
                        <p className="text-sm font-medium">{config.label}</p>
                        <p className="text-xs text-muted-foreground">Current Status</p>
                    </div>
                </div>

                {/* Priority & Badges */}
                <div className="flex gap-2 flex-wrap">
                    <Badge className={cn("text-xs", priorityColors[task.priority])}>
                        {task.priority} Priority
                    </Badge>
                    {task.assignee && (
                        <Badge variant="outline" className="text-xs">
                            <User className="h-3 w-3 mr-1" />
                            {task.assignee}
                        </Badge>
                    )}
                </div>

                <Separator />

                {/* Description */}
                {task.description && (
                    <div>
                        <p className="text-sm font-medium mb-1">Description</p>
                        <p className="text-sm text-muted-foreground">{task.description}</p>
                    </div>
                )}

                {/* Time Info */}
                <div className="grid grid-cols-2 gap-3">
                    {task.estimated_hours !== undefined && task.estimated_hours > 0 && (
                        <div>
                            <p className="text-xs text-muted-foreground">Estimated</p>
                            <p className="text-sm font-medium">{task.estimated_hours}h</p>
                        </div>
                    )}
                    {task.actual_hours !== undefined && task.actual_hours > 0 && (
                        <div>
                            <p className="text-xs text-muted-foreground">Actual</p>
                            <p className="text-sm font-medium">{task.actual_hours}h</p>
                        </div>
                    )}
                    {task.deadline && (
                        <div className="col-span-2">
                            <p className="text-xs text-muted-foreground flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                Deadline
                            </p>
                            <p className="text-sm font-medium">
                                {format(new Date(task.deadline), "MMM d, yyyy")}
                            </p>
                        </div>
                    )}
                </div>

                <Separator />

                {/* Dependencies */}
                {dependencyTitles.length > 0 && (
                    <div>
                        <p className="text-sm font-medium mb-2 flex items-center gap-1">
                            <ArrowRight className="h-3 w-3 rotate-180" />
                            Depends On ({dependencyTitles.length})
                        </p>
                        <div className="space-y-1">
                            {dependencyTitles.map((title, i) => (
                                <div
                                    key={i}
                                    className="text-xs bg-muted px-2 py-1 rounded line-clamp-1"
                                >
                                    {title}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Dependents */}
                {dependentTitles.length > 0 && (
                    <div>
                        <p className="text-sm font-medium mb-2 flex items-center gap-1">
                            <ArrowRight className="h-3 w-3" />
                            Blocks ({dependentTitles.length})
                        </p>
                        <div className="space-y-1">
                            {dependentTitles.map((title, i) => (
                                <div
                                    key={i}
                                    className="text-xs bg-muted px-2 py-1 rounded line-clamp-1"
                                >
                                    {title}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Timestamps */}
                <div className="text-xs text-muted-foreground space-y-1">
                    <p>Created: {format(new Date(task.created_at), "MMM d, yyyy HH:mm")}</p>
                    <p>Updated: {format(new Date(task.updated_at), "MMM d, yyyy HH:mm")}</p>
                </div>
            </CardContent>

            {/* Action Buttons */}
            <div className="p-4 border-t flex-shrink-0 space-y-2">
                <div className="flex gap-2">
                    {canStart && onStart && (
                        <Button
                            variant="outline"
                            className="flex-1"
                            onClick={() => onStart(task.id)}
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <>
                                    <Play className="h-4 w-4 mr-1" />
                                    Start
                                </>
                            )}
                        </Button>
                    )}
                    {canComplete && onComplete && task.status !== TaskStatus.PENDING && (
                        <Button
                            className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                            onClick={() => onComplete(task.id)}
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <>
                                    <CheckCircle2 className="h-4 w-4 mr-1" />
                                    Complete
                                </>
                            )}
                        </Button>
                    )}
                </div>
                <div className="flex gap-2">
                    {task.status !== TaskStatus.BLOCKED && onBlock && (
                        <Button
                            variant="outline"
                            size="sm"
                            className="flex-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                            onClick={() => onBlock(task.id)}
                            disabled={isLoading}
                        >
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Block
                        </Button>
                    )}
                    {task.status !== TaskStatus.PENDING && onReset && (
                        <Button
                            variant="outline"
                            size="sm"
                            className="flex-1"
                            onClick={() => onReset(task.id)}
                            disabled={isLoading}
                        >
                            <RotateCcw className="h-3 w-3 mr-1" />
                            Reset
                        </Button>
                    )}
                </div>
            </div>
        </Card>
    );
}
