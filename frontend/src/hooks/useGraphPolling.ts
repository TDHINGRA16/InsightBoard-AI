"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { GraphData, GraphNode, GraphEdge, Job, Task } from "@/types";
import { JobStatus, TaskStatus } from "@/types/enums";

interface UseGraphPollingOptions {
    transcriptId: string;
    enabled?: boolean;
    pollingInterval?: number;
    onTasksUpdate?: (tasks: Task[]) => void;
    onJobStatusChange?: (jobId: string, status: JobStatus) => void;
}

interface PollingState {
    graphData: GraphData | null;
    criticalPath: string[];
    tasks: Task[];
    activeJobs: Job[];
    isLoading: boolean;
    error: string | null;
    lastUpdated: Date | null;
    completionPercentage: number;
}

/**
 * Hook for polling graph data and job statuses with automatic cleanup.
 * Implements smart polling that only fetches active jobs.
 */
export function useGraphPolling({
    transcriptId,
    enabled = true,
    pollingInterval = 2000,
    onTasksUpdate,
    onJobStatusChange,
}: UseGraphPollingOptions) {
    const [state, setState] = useState<PollingState>({
        graphData: null,
        criticalPath: [],
        tasks: [],
        activeJobs: [],
        isLoading: true,
        error: null,
        lastUpdated: null,
        completionPercentage: 0,
    });

    const abortControllerRef = useRef<AbortController | null>(null);
    const pollingRef = useRef<NodeJS.Timeout | null>(null);
    const mountedRef = useRef(true);

    /**
     * Fetch initial graph data from backend
     */
    const fetchGraphData = useCallback(async () => {
        if (!transcriptId || !mountedRef.current) return;

        try {
            // Abort previous request if any
            abortControllerRef.current?.abort();
            abortControllerRef.current = new AbortController();

            const [graphResponse, tasksResponse, jobsResponse] = await Promise.all([
                api.getGraph(transcriptId),
                api.getTasks({ transcript_id: transcriptId, page_size: 100 }),
                api.getJobs({ transcript_id: transcriptId }),
            ]);

            if (!mountedRef.current) return;

            const graphData = graphResponse.data?.data;
            const tasks = tasksResponse.data?.data || [];
            const jobs = jobsResponse.data?.data || [];

            // Calculate completion percentage
            const completedTasks = tasks.filter(
                (t: Task) => t.status === TaskStatus.COMPLETED
            ).length;
            const completionPercentage =
                tasks.length > 0 ? Math.round((completedTasks / tasks.length) * 100) : 0;

            // Filter active jobs (queued or processing)
            const activeJobs = jobs.filter(
                (j: Job) =>
                    j.status === JobStatus.QUEUED || j.status === JobStatus.PROCESSING
            );

            setState((prev) => ({
                ...prev,
                graphData: graphData?.data || null,
                criticalPath: graphResponse.data?.critical_path || [],
                tasks,
                activeJobs,
                isLoading: false,
                error: null,
                lastUpdated: new Date(),
                completionPercentage,
            }));

            onTasksUpdate?.(tasks);
        } catch (error: any) {
            if (error.name === "AbortError") return;
            if (!mountedRef.current) return;

            setState((prev) => ({
                ...prev,
                isLoading: false,
                error: error.message || "Failed to fetch graph data",
            }));
        }
    }, [transcriptId, onTasksUpdate]);

    /**
     * Poll active job statuses
     */
    const pollJobStatuses = useCallback(async () => {
        if (!mountedRef.current || state.activeJobs.length === 0) return;

        try {
            const jobPromises = state.activeJobs.map((job) =>
                api.getJobStatus(job.id).catch(() => null)
            );

            const results = await Promise.all(jobPromises);

            if (!mountedRef.current) return;

            let hasChanges = false;
            const updatedJobs = state.activeJobs.map((job, index) => {
                const result = results[index];
                if (result?.data?.data) {
                    const newStatus = result.data.data.status;
                    if (newStatus !== job.status) {
                        hasChanges = true;
                        onJobStatusChange?.(job.id, newStatus);
                    }
                    return { ...job, ...result.data.data };
                }
                return job;
            });

            // If any job completed or failed, refetch full graph data
            const completedOrFailed = updatedJobs.filter(
                (j) =>
                    j.status === JobStatus.COMPLETED || j.status === JobStatus.FAILED
            );

            if (completedOrFailed.length > 0) {
                await fetchGraphData();
            } else if (hasChanges) {
                setState((prev) => ({
                    ...prev,
                    activeJobs: updatedJobs.filter(
                        (j) =>
                            j.status === JobStatus.QUEUED ||
                            j.status === JobStatus.PROCESSING
                    ),
                }));
            }
        } catch (error) {
            // Silently fail polling errors
            console.warn("Job polling error:", error);
        }
    }, [state.activeJobs, fetchGraphData, onJobStatusChange]);

    /**
     * Start polling
     */
    const startPolling = useCallback(() => {
        if (pollingRef.current) return;

        pollingRef.current = setInterval(() => {
            if (state.activeJobs.length > 0) {
                pollJobStatuses();
            }
        }, pollingInterval);
    }, [pollJobStatuses, pollingInterval, state.activeJobs.length]);

    /**
     * Stop polling
     */
    const stopPolling = useCallback(() => {
        if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
    }, []);

    /**
     * Refresh data manually
     */
    const refresh = useCallback(async () => {
        setState((prev) => ({ ...prev, isLoading: true }));
        await fetchGraphData();
    }, [fetchGraphData]);

    // Initial fetch
    useEffect(() => {
        mountedRef.current = true;

        if (enabled && transcriptId) {
            fetchGraphData();
        }

        return () => {
            mountedRef.current = false;
            abortControllerRef.current?.abort();
            stopPolling();
        };
    }, [enabled, transcriptId, fetchGraphData, stopPolling]);

    // Start/stop polling based on active jobs
    useEffect(() => {
        if (enabled && state.activeJobs.length > 0) {
            startPolling();
        } else {
            stopPolling();
        }

        return stopPolling;
    }, [enabled, state.activeJobs.length, startPolling, stopPolling]);

    return {
        ...state,
        refresh,
        startPolling,
        stopPolling,
    };
}
