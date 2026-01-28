"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { Job, JobStatus } from "@/types";

interface UseJobPollingOptions {
    interval?: number;
    onComplete?: (result: any) => void;
    onError?: (error: string) => void;
}

export const useJobPolling = (
    jobId: string | null,
    options: UseJobPollingOptions = {}
) => {
    const { interval = 2000, onComplete, onError } = options;

    const [job, setJob] = useState<Job | null>(null);
    const [status, setStatus] = useState<JobStatus>(JobStatus.QUEUED);
    const [progress, setProgress] = useState(0);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [isPolling, setIsPolling] = useState(false);

    const checkStatus = useCallback(async () => {
        if (!jobId) return;

        try {
            const response = await api.getJobStatus(jobId);
            const jobData = response.data.data;

            setJob(jobData);
            setStatus(jobData.status);
            setProgress(jobData.progress || 0);

            if (jobData.status === JobStatus.COMPLETED) {
                setResult(jobData.result);
                setIsPolling(false);
                onComplete?.(jobData.result);
            } else if (jobData.status === JobStatus.FAILED) {
                setError(jobData.error_message || "Job failed");
                setIsPolling(false);
                onError?.(jobData.error_message || "Job failed");
            }
        } catch (err: any) {
            setError(err.message);
            setIsPolling(false);
            onError?.(err.message);
        }
    }, [jobId, onComplete, onError]);

    useEffect(() => {
        if (!jobId) {
            setIsPolling(false);
            return;
        }

        setIsPolling(true);
        setError(null);
        setResult(null);
        setProgress(0);
        setStatus(JobStatus.QUEUED);

        // Initial check
        checkStatus();

        // Set up polling
        const pollInterval = setInterval(() => {
            if (status === JobStatus.COMPLETED || status === JobStatus.FAILED) {
                clearInterval(pollInterval);
                return;
            }
            checkStatus();
        }, interval);

        return () => {
            clearInterval(pollInterval);
        };
    }, [jobId, interval, checkStatus, status]);

    const reset = useCallback(() => {
        setJob(null);
        setStatus(JobStatus.QUEUED);
        setProgress(0);
        setResult(null);
        setError(null);
        setIsPolling(false);
    }, []);

    return {
        job,
        status,
        progress,
        result,
        error,
        isPolling,
        isCompleted: status === JobStatus.COMPLETED,
        isFailed: status === JobStatus.FAILED,
        isProcessing: status === JobStatus.PROCESSING,
        reset,
    };
};
