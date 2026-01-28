"use client";

import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { Clock, User, GitBranch, MoreVertical, Eye, Edit, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Task } from "@/types";
import { StatusBadge, PriorityBadge } from "./TaskBadges";

interface TaskCardProps {
    task: Task;
    onEdit?: (task: Task) => void;
    onDelete?: (id: string) => void;
    showTranscript?: boolean;
}

export function TaskCard({
    task,
    onEdit,
    onDelete,
    showTranscript = false,
}: TaskCardProps) {
    return (
        <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-start justify-between pb-2">
                <div className="flex-1 min-w-0">
                    <Link
                        href={`/tasks/${task.id}`}
                        className="font-semibold hover:text-primary transition-colors line-clamp-1"
                    >
                        {task.title}
                    </Link>
                    {task.description && (
                        <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                            {task.description}
                        </p>
                    )}
                </div>

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="flex-shrink-0">
                            <MoreVertical className="h-4 w-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuItem asChild>
                            <Link href={`/tasks/${task.id}`}>
                                <Eye className="h-4 w-4 mr-2" />
                                View Details
                            </Link>
                        </DropdownMenuItem>
                        {onEdit && (
                            <DropdownMenuItem onClick={() => onEdit(task)}>
                                <Edit className="h-4 w-4 mr-2" />
                                Edit
                            </DropdownMenuItem>
                        )}
                        {onDelete && (
                            <DropdownMenuItem
                                onClick={() => onDelete(task.id)}
                                className="text-destructive"
                            >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                            </DropdownMenuItem>
                        )}
                    </DropdownMenuContent>
                </DropdownMenu>
            </CardHeader>

            <CardContent>
                {/* Badges */}
                <div className="flex gap-2 mb-3">
                    <StatusBadge status={task.status} />
                    <PriorityBadge priority={task.priority} />
                </div>

                {/* Meta info */}
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                    {task.assignee && (
                        <div className="flex items-center gap-1">
                            <User className="h-4 w-4" />
                            <span>{task.assignee}</span>
                        </div>
                    )}
                    {task.estimated_hours && (
                        <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            <span>{task.estimated_hours}h</span>
                        </div>
                    )}
                    {task.dependencies && task.dependencies.length > 0 && (
                        <div className="flex items-center gap-1">
                            <GitBranch className="h-4 w-4" />
                            <span>{task.dependencies.length} deps</span>
                        </div>
                    )}
                </div>

                {/* Deadline */}
                {task.deadline && (
                    <p className="text-sm text-muted-foreground mt-2">
                        Due{" "}
                        {formatDistanceToNow(new Date(task.deadline), { addSuffix: true })}
                    </p>
                )}
            </CardContent>
        </Card>
    );
}
