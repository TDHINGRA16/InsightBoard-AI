import axios, { AxiosInstance } from "axios";
import { supabase } from "./supabase";

const createApiClient = (): AxiosInstance => {
    const client = axios.create({
        baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
        headers: {
            "Content-Type": "application/json",
        },
    });

    // Request interceptor: attach JWT
    client.interceptors.request.use(
        async (config) => {
            const {
                data: { session },
            } = await supabase.auth.getSession();

            if (session?.access_token) {
                config.headers.Authorization = `Bearer ${session.access_token}`;
            }

            return config;
        },
        (error) => Promise.reject(error)
    );

    // Response interceptor: handle 401
    client.interceptors.response.use(
        (response) => response,
        (error) => {
            if (error.response?.status === 401) {
                // Redirect to login
                if (typeof window !== "undefined") {
                    window.location.href = "/login";
                }
            }
            return Promise.reject(error);
        }
    );

    return client;
};

export const apiClient = createApiClient();

// Typed endpoints
export const api = {
    // Transcripts
    uploadTranscript: (formData: FormData) =>
        apiClient.post("/transcripts/upload", formData, {
            headers: { "Content-Type": "multipart/form-data" },
        }),
    getTranscripts: (params?: { page?: number; page_size?: number; status?: string }) =>
        apiClient.get("/transcripts", { params }),
    getTranscript: (id: string) => apiClient.get(`/transcripts/${id}`),
    deleteTranscript: (id: string) => apiClient.delete(`/transcripts/${id}`),

    // Tasks
    getTasks: (params?: {
        transcript_id?: string;
        status?: string;
        priority?: string;
        page?: number;
        page_size?: number;
    }) => apiClient.get("/tasks", { params }),
    getTask: (id: string) => apiClient.get(`/tasks/${id}`),
    createTask: (data: any) => apiClient.post("/tasks", data),
    updateTask: (id: string, data: any) => apiClient.put(`/tasks/${id}`, data),
    deleteTask: (id: string) => apiClient.delete(`/tasks/${id}`),

    // Dependencies
    getDependencies: (params?: { task_id?: string; transcript_id?: string }) =>
        apiClient.get("/dependencies", { params }),
    createDependency: (data: { task_id: string; depends_on_task_id: string; dependency_type?: string }) =>
        apiClient.post("/dependencies", data),
    deleteDependency: (id: string) => apiClient.delete(`/dependencies/${id}`),

    // Analysis
    startAnalysis: (transcriptId: string, options?: { force?: boolean; idempotencyKey?: string }) => {
        // Use stable key based on transcript ID for true idempotency
        // When force=true, generate a unique key to allow re-analysis
        const key = options?.idempotencyKey
            || (options?.force ? `analyze-${transcriptId}-${Date.now()}` : `analyze-${transcriptId}`);

        return apiClient.post("/analysis/start", {
            transcript_id: transcriptId,
            idempotency_key: key,
            force: options?.force || false,
        });
    },
    retryAnalysis: (transcriptId: string) =>
        apiClient.post(`/analysis/retry/${transcriptId}`),

    // Jobs
    getJobs: (params?: { status?: string; transcript_id?: string }) =>
        apiClient.get("/jobs", { params }),
    getJobStatus: (jobId: string) => apiClient.get(`/jobs/${jobId}`),
    cancelJob: (jobId: string) => apiClient.post(`/jobs/${jobId}/cancel`),

    // Graphs
    getGraph: (transcriptId: string, useCache = true) =>
        apiClient.get(`/graphs/${transcriptId}`, { params: { use_cache: useCache } }),
    getGraphVisualization: (transcriptId: string, useCache = true) =>
        apiClient.get(`/graphs/${transcriptId}`, { params: { use_cache: useCache } }),
    getCriticalPath: (transcriptId: string) =>
        apiClient.get(`/graphs/${transcriptId}/critical-path`),
    getBottlenecks: (transcriptId: string) =>
        apiClient.get(`/graphs/${transcriptId}/bottlenecks`),
    refreshGraph: (transcriptId: string) =>
        apiClient.post(`/graphs/${transcriptId}/refresh`),

    // Task Actions
    completeTask: (taskId: string) =>
        apiClient.post(`/tasks/${taskId}/complete`),

    // Export
    exportJson: (transcriptId: string) =>
        apiClient.get(`/export/${transcriptId}/json`),
    exportCsv: (transcriptId: string) =>
        apiClient.get(`/export/${transcriptId}/csv`, { responseType: "blob" }),
    exportGantt: (transcriptId: string) =>
        apiClient.get(`/export/${transcriptId}/gantt`),

    // Analytics
    getDashboardAnalytics: () => apiClient.get("/analytics/dashboard"),
    getQuickSummary: () => apiClient.get("/analytics/summary"),
    getTranscriptAnalytics: (transcriptId: string) =>
        apiClient.get(`/analytics/transcript/${transcriptId}`),

    // Webhooks
    getWebhooks: () => apiClient.get("/webhooks"),
    createWebhook: (data: { event_type: string; endpoint_url: string; description?: string }) =>
        apiClient.post("/webhooks", data),
    getWebhook: (id: string) => apiClient.get(`/webhooks/${id}`),
    updateWebhook: (id: string, data: { endpoint_url?: string; is_active?: boolean }) =>
        apiClient.patch(`/webhooks/${id}`, data),
    deleteWebhook: (id: string) => apiClient.delete(`/webhooks/${id}`),
    testWebhook: (id: string) => apiClient.post(`/webhooks/${id}/test`),
    getWebhookEventTypes: () => apiClient.get("/webhooks/events"),
};
