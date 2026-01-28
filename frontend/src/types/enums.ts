// Task Status
export enum TaskStatus {
    PENDING = "pending",
    IN_PROGRESS = "in_progress",
    COMPLETED = "completed",
    BLOCKED = "blocked",
}

// Task Priority
export enum TaskPriority {
    LOW = "low",
    MEDIUM = "medium",
    HIGH = "high",
    CRITICAL = "critical",
}

// Transcript Status
export enum TranscriptStatus {
    UPLOADED = "uploaded",
    ANALYZING = "analyzing",
    ANALYZED = "analyzed",
    FAILED = "failed",
}

// Job Status
export enum JobStatus {
    QUEUED = "queued",
    PROCESSING = "processing",
    COMPLETED = "completed",
    FAILED = "failed",
}

// Job Type
export enum JobType {
    ANALYZE = "analyze",
    EXPORT = "export",
    OPTIMIZE = "optimize",
}

// Dependency Type
export enum DependencyType {
    BLOCKS = "blocks",
    PRECEDES = "precedes",
    PARENT_OF = "parent_of",
    RELATED_TO = "related_to",
}

// Webhook Event Type
export enum WebhookEventType {
    ANALYSIS_COMPLETED = "analysis.completed",
    ANALYSIS_FAILED = "analysis.failed",
    TASK_CREATED = "task.created",
    TASK_UPDATED = "task.updated",
    TASK_COMPLETED = "task.completed",
    EXPORT_COMPLETED = "export.completed",
}
