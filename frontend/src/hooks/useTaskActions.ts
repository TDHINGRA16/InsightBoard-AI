"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import { Task } from "@/types";
import { TaskStatus } from "@/types/enums";
import { toast } from "@/lib/toast";

interface UseTaskActionsOptions {
    onTaskUpdated?: (task: Task) => void;
    onError?: (error: string) => void;
}

interface TaskActionState {
    isLoading: boolean;
    loadingTaskId: string | null;
    error: string | null;
}

/**
 * Hook for task actions with loading states and error handling.
 */
export function useTaskActions({ onTaskUpdated, onError }: UseTaskActionsOptions = {}) {
    const [state, setState] = useState<TaskActionState>({
        isLoading: false,
        loadingTaskId: null,
        error: null,
    });

    /**
     * Complete a task (mark as completed)
     */
    const completeTask = useCallback(
        async (taskId: string, taskTitle?: string) => {
            setState({ isLoading: true, loadingTaskId: taskId, error: null });

            try {
                const response = await api.updateTask(taskId, {
                    status: TaskStatus.COMPLETED,
                });

                if (response.data?.success) {
                    toast.success(`Task "${taskTitle || "Task"}" marked as completed`);
                    onTaskUpdated?.(response.data.data);
                    setState({ isLoading: false, loadingTaskId: null, error: null });
                    return response.data.data;
                } else {
                    throw new Error("Failed to complete task");
                }
            } catch (error: any) {
                const message = error.response?.data?.message || error.message || "Failed to complete task";
                setState({ isLoading: false, loadingTaskId: null, error: message });
                toast.error(message);
                onError?.(message);
                return null;
            }
        },
        [onTaskUpdated, onError]
    );

    /**
     * Start a task (mark as in_progress)
     */
    const startTask = useCallback(
        async (taskId: string, taskTitle?: string) => {
            setState({ isLoading: true, loadingTaskId: taskId, error: null });

            try {
                const response = await api.updateTask(taskId, {
                    status: TaskStatus.IN_PROGRESS,
                });

                if (response.data?.success) {
                    toast.success(`Task "${taskTitle || "Task"}" started`);
                    onTaskUpdated?.(response.data.data);
                    setState({ isLoading: false, loadingTaskId: null, error: null });
                    return response.data.data;
                } else {
                    throw new Error("Failed to start task");
                }
            } catch (error: any) {
                const message = error.response?.data?.message || error.message || "Failed to start task";
                setState({ isLoading: false, loadingTaskId: null, error: message });
                toast.error(message);
                onError?.(message);
                return null;
            }
        },
        [onTaskUpdated, onError]
    );

    /**
     * Block a task (mark as blocked)
     */
    const blockTask = useCallback(
        async (taskId: string, taskTitle?: string) => {
            setState({ isLoading: true, loadingTaskId: taskId, error: null });

            try {
                const response = await api.updateTask(taskId, {
                    status: TaskStatus.BLOCKED,
                });

                if (response.data?.success) {
                    toast.warning(`Task "${taskTitle || "Task"}" marked as blocked`);
                    onTaskUpdated?.(response.data.data);
                    setState({ isLoading: false, loadingTaskId: null, error: null });
                    return response.data.data;
                } else {
                    throw new Error("Failed to block task");
                }
            } catch (error: any) {
                const message = error.response?.data?.message || error.message || "Failed to block task";
                setState({ isLoading: false, loadingTaskId: null, error: message });
                toast.error(message);
                onError?.(message);
                return null;
            }
        },
        [onTaskUpdated, onError]
    );

    /**
     * Reset task to pending
     */
    const resetTask = useCallback(
        async (taskId: string, taskTitle?: string) => {
            setState({ isLoading: true, loadingTaskId: taskId, error: null });

            try {
                const response = await api.updateTask(taskId, {
                    status: TaskStatus.PENDING,
                });

                if (response.data?.success) {
                    toast.info(`Task "${taskTitle || "Task"}" reset to pending`);
                    onTaskUpdated?.(response.data.data);
                    setState({ isLoading: false, loadingTaskId: null, error: null });
                    return response.data.data;
                } else {
                    throw new Error("Failed to reset task");
                }
            } catch (error: any) {
                const message = error.response?.data?.message || error.message || "Failed to reset task";
                setState({ isLoading: false, loadingTaskId: null, error: message });
                toast.error(message);
                onError?.(message);
                return null;
            }
        },
        [onTaskUpdated, onError]
    );

    /**
     * Update task with custom data
     */
    const updateTask = useCallback(
        async (taskId: string, data: Partial<Task>) => {
            setState({ isLoading: true, loadingTaskId: taskId, error: null });

            try {
                const response = await api.updateTask(taskId, data);

                if (response.data?.success) {
                    toast.success("Task updated");
                    onTaskUpdated?.(response.data.data);
                    setState({ isLoading: false, loadingTaskId: null, error: null });
                    return response.data.data;
                } else {
                    throw new Error("Failed to update task");
                }
            } catch (error: any) {
                const message = error.response?.data?.message || error.message || "Failed to update task";
                setState({ isLoading: false, loadingTaskId: null, error: message });
                toast.error(message);
                onError?.(message);
                return null;
            }
        },
        [onTaskUpdated, onError]
    );

    return {
        ...state,
        completeTask,
        startTask,
        blockTask,
        resetTask,
        updateTask,
    };
}
