"use client";

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";
import { TaskStatus, TaskPriority } from "@/types";
import { useUIStore } from "@/store";

export function TaskFilters() {
    const {
        taskStatusFilter,
        taskPriorityFilter,
        setTaskStatusFilter,
        setTaskPriorityFilter,
        clearFilters,
    } = useUIStore();

    const hasFilters = taskStatusFilter || taskPriorityFilter;

    return (
        <div className="flex flex-wrap gap-4 items-center">
            {/* Status Filter */}
            <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Status:</span>
                <Select
                    value={taskStatusFilter || "all"}
                    onValueChange={(value) =>
                        setTaskStatusFilter(value === "all" ? null : value)
                    }
                >
                    <SelectTrigger className="w-[140px]">
                        <SelectValue placeholder="All" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All</SelectItem>
                        <SelectItem value={TaskStatus.PENDING}>Pending</SelectItem>
                        <SelectItem value={TaskStatus.IN_PROGRESS}>In Progress</SelectItem>
                        <SelectItem value={TaskStatus.COMPLETED}>Completed</SelectItem>
                        <SelectItem value={TaskStatus.BLOCKED}>Blocked</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Priority Filter */}
            <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Priority:</span>
                <Select
                    value={taskPriorityFilter || "all"}
                    onValueChange={(value) =>
                        setTaskPriorityFilter(value === "all" ? null : value)
                    }
                >
                    <SelectTrigger className="w-[140px]">
                        <SelectValue placeholder="All" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All</SelectItem>
                        <SelectItem value={TaskPriority.LOW}>Low</SelectItem>
                        <SelectItem value={TaskPriority.MEDIUM}>Medium</SelectItem>
                        <SelectItem value={TaskPriority.HIGH}>High</SelectItem>
                        <SelectItem value={TaskPriority.CRITICAL}>Critical</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Clear Filters */}
            {hasFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                    <X className="h-4 w-4 mr-1" />
                    Clear
                </Button>
            )}
        </div>
    );
}
