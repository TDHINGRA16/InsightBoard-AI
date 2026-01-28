"use client";

import { useJobPolling } from "@/hooks";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle, XCircle, Loader2, Clock } from "lucide-react";
import { JobStatus } from "@/types";
import { cn } from "@/lib/utils";

interface AnalysisProgressProps {
    jobId: string;
    onComplete?: (result: any) => void;
    onError?: (error: string) => void;
}

const statusIcons = {
    [JobStatus.QUEUED]: Clock,
    [JobStatus.PROCESSING]: Loader2,
    [JobStatus.COMPLETED]: CheckCircle,
    [JobStatus.FAILED]: XCircle,
};

const statusMessages = {
    [JobStatus.QUEUED]: "Waiting in queue...",
    [JobStatus.PROCESSING]: "Analyzing transcript...",
    [JobStatus.COMPLETED]: "Analysis complete!",
    [JobStatus.FAILED]: "Analysis failed",
};

export function AnalysisProgress({
    jobId,
    onComplete,
    onError,
}: AnalysisProgressProps) {
    const { status, progress, error, isCompleted, isFailed } = useJobPolling(
        jobId,
        { onComplete, onError }
    );

    const Icon = statusIcons[status];

    return (
        <Card
            className={cn(
                "border-2",
                isCompleted && "border-green-500",
                isFailed && "border-destructive"
            )}
        >
            <CardHeader className="pb-2">
                <div className="flex items-center gap-3">
                    <Icon
                        className={cn(
                            "h-6 w-6",
                            status === JobStatus.PROCESSING && "animate-spin",
                            isCompleted && "text-green-500",
                            isFailed && "text-destructive"
                        )}
                    />
                    <CardTitle className="text-lg">{statusMessages[status]}</CardTitle>
                </div>
            </CardHeader>

            <CardContent>
                <Progress value={progress} className="h-2 mb-2" />
                <p className="text-sm text-muted-foreground">
                    {progress}% complete
                </p>

                {error && (
                    <p className="text-sm text-destructive mt-2">{error}</p>
                )}

                {isCompleted && (
                    <p className="text-sm text-green-600 mt-2">
                        Tasks and dependencies have been extracted. View them in the
                        transcript details.
                    </p>
                )}
            </CardContent>
        </Card>
    );
}
