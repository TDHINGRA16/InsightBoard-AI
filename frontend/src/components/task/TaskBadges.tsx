"use client";

import { Badge } from "@/components/ui/badge";
import { TaskStatus, TaskPriority } from "@/types";
import { cn } from "@/lib/utils";

interface TaskBadgesProps {
    status?: TaskStatus;
    priority?: TaskPriority;
}

const statusColors: Record<TaskStatus, string> = {
    [TaskStatus.PENDING]: "bg-slate-100 text-slate-800",
    [TaskStatus.IN_PROGRESS]: "bg-blue-100 text-blue-800",
    [TaskStatus.COMPLETED]: "bg-green-100 text-green-800",
    [TaskStatus.BLOCKED]: "bg-red-100 text-red-800",
};

const statusLabels: Record<TaskStatus, string> = {
    [TaskStatus.PENDING]: "Pending",
    [TaskStatus.IN_PROGRESS]: "In Progress",
    [TaskStatus.COMPLETED]: "Completed",
    [TaskStatus.BLOCKED]: "Blocked",
};

const priorityColors: Record<TaskPriority, string> = {
    [TaskPriority.LOW]: "bg-gray-100 text-gray-800",
    [TaskPriority.MEDIUM]: "bg-yellow-100 text-yellow-800",
    [TaskPriority.HIGH]: "bg-orange-100 text-orange-800",
    [TaskPriority.CRITICAL]: "bg-red-100 text-red-800",
};

const priorityLabels: Record<TaskPriority, string> = {
    [TaskPriority.LOW]: "Low",
    [TaskPriority.MEDIUM]: "Medium",
    [TaskPriority.HIGH]: "High",
    [TaskPriority.CRITICAL]: "Critical",
};

export function StatusBadge({ status }: { status: TaskStatus }) {
    return (
        <Badge className={cn("font-medium", statusColors[status])}>
            {statusLabels[status]}
        </Badge>
    );
}

export function PriorityBadge({ priority }: { priority: TaskPriority }) {
    return (
        <Badge className={cn("font-medium", priorityColors[priority])}>
            {priorityLabels[priority]}
        </Badge>
    );
}

export function TaskBadges({ status, priority }: TaskBadgesProps) {
    return (
        <div className="flex gap-2">
            {status && <StatusBadge status={status} />}
            {priority && <PriorityBadge priority={priority} />}
        </div>
    );
}
