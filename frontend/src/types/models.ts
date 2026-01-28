import {
    TaskStatus,
    TaskPriority,
    TranscriptStatus,
    JobStatus,
    JobType,
    DependencyType,
    WebhookEventType,
} from "./enums";

// Task Model
export interface Task {
    id: string;
    transcript_id: string;
    title: string;
    description?: string;
    deadline?: string;
    priority: TaskPriority;
    status: TaskStatus;
    assignee?: string;
    estimated_hours?: number;
    actual_hours?: number;
    position_x?: number;
    position_y?: number;
    created_at: string;
    updated_at: string;
    dependencies?: Dependency[];
    dependents?: Dependency[];
}

// Transcript Model
export interface Transcript {
    id: string;
    user_id: string;
    filename: string;
    file_type: string;
    size_bytes: number;
    content?: string;
    content_hash: string;
    status: TranscriptStatus;
    analysis_result?: any;
    error_message?: string;
    created_at: string;
    updated_at: string;
    tasks?: Task[];
}

// Dependency Model
export interface Dependency {
    id: string;
    task_id: string;
    depends_on_task_id: string;
    dependency_type: DependencyType;
    lag_days: number;
    created_at: string;
    task_title?: string;
    depends_on_title?: string;
    task?: Task;
    depends_on_task?: Task;
}

// Job Model
export interface Job {
    id: string;
    user_id: string;
    transcript_id: string;
    job_type: JobType;
    status: JobStatus;
    result?: any;
    error_message?: string;
    idempotency_key: string;
    progress: number;
    started_at?: string;
    completed_at?: string;
    created_at: string;
}

// Graph Model
export interface Graph {
    id: string;
    transcript_id: string;
    nodes_count: number;
    edges_count: number;
    critical_path?: string[];
    critical_path_length?: number;
    total_duration_days?: number;
    slack_data?: Record<string, number>;
    graph_data?: any;
    created_at: string;
    updated_at: string;
}

// Webhook Model
export interface Webhook {
    id: string;
    user_id: string;
    event_type: WebhookEventType;
    endpoint_url: string;
    is_active: boolean;
    secret_key?: string;
    description?: string;
    failed_attempts: number;
    last_triggered_at?: string;
    last_error?: string;
    created_at: string;
}

// React Flow Types
export interface GraphNode {
    id: string;
    type: string;
    position: { x: number; y: number };
    data: {
        label: string;
        title: string;
        priority: TaskPriority;
        status: TaskStatus;
        assignee?: string;
        estimated_hours?: number;
        is_critical?: boolean;
        slack?: number;
    };
}

export interface GraphEdge {
    id: string;
    source: string;
    target: string;
    type?: string;
    animated?: boolean;
    label?: string;
    style?: Record<string, any>;
}

export interface GraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

// Critical Path Response
export interface CriticalPathResponse {
    critical_path: string[];
    total_duration_hours: number;
    total_duration_days: number;
    tasks: Task[];
}

// Bottleneck Response
export interface Bottleneck {
    task_id: string;
    title: string;
    in_degree: number;
    out_degree: number;
    total_connections: number;
    score: number;
}

// Analytics Response
export interface DashboardAnalytics {
    transcripts: {
        total: number;
        by_status: Record<string, number>;
    };
    tasks: {
        total: number;
        by_status: Record<string, number>;
        by_priority: Record<string, number>;
    };
    dependencies: {
        total: number;
        average_per_task: number;
    };
    jobs: {
        total: number;
        by_status: Record<string, number>;
    };
    metrics: {
        average_critical_path_hours: number;
    };
}

// API Response Types
export interface ApiResponse<T> {
    success: boolean;
    data: T;
    message?: string;
}

export interface PaginatedResponse<T> {
    success: boolean;
    data: T[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}
