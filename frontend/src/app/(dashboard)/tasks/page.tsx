"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader, EmptyState, Loading } from "@/components/common";
import { TaskCard, TaskFilters } from "@/components/task";
import { ListTodo } from "lucide-react";
import { Task } from "@/types";
import { useUIStore } from "@/store";
import { toast } from "sonner";

export default function TasksPage() {
    const queryClient = useQueryClient();
    const { taskStatusFilter, taskPriorityFilter } = useUIStore();

    const { data, isLoading } = useQuery({
        queryKey: ["tasks", { status: taskStatusFilter, priority: taskPriorityFilter }],
        queryFn: async () => {
            const params: any = {};
            if (taskStatusFilter) params.status = taskStatusFilter;
            if (taskPriorityFilter) params.priority = taskPriorityFilter;
            const response = await api.getTasks(params);
            return response.data;
        },
    });

    const deleteTaskMutation = useMutation({
        mutationFn: async (id: string) => {
            await api.deleteTask(id);
            return id;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tasks"] });
            toast.success("Task deleted");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to delete task");
        },
    });

    const tasks: Task[] = data?.data || [];

    if (isLoading) {
        return <Loading text="Loading tasks..." />;
    }

    return (
        <div>
            <PageHeader
                title="Tasks"
                description="View and manage extracted tasks"
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Tasks" },
                ]}
            />

            {/* Filters */}
            <div className="mb-6">
                <TaskFilters />
            </div>

            {tasks.length === 0 ? (
                <EmptyState
                    icon={<ListTodo className="h-8 w-8 text-muted-foreground" />}
                    title="No tasks found"
                    description="Tasks will appear here after you analyze a transcript."
                />
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {tasks.map((task) => (
                        <TaskCard
                            key={task.id}
                            task={task}
                            onDelete={(id) => deleteTaskMutation.mutate(id)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
