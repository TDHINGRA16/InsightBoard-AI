"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import { TaskCard, StatusBadge } from "@/components/task";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
    FileText,
    Play,
    GitBranch,
    Clock,
    Download,
    RefreshCw,
} from "lucide-react";
import { formatDistanceToNow, format, parseISO } from "date-fns";
import { TranscriptStatus } from "@/types";
import { toast } from "@/lib/toast";

export default function TranscriptDetailPage() {
    const { id } = useParams<{ id: string }>();

    const exportCsvMutation = useMutation({
        mutationFn: async () => {
            const res = await api.exportCsv(id);
            return res.data as Blob;
        },
        onSuccess: (blob) => {
            const baseName = (data?.filename || `transcript-${id}`).replace(/\.[^/.]+$/, "");
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${baseName}.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
            toast.success("CSV downloaded");
        },
        onError: (error: any) => {
            toast.error(error?.response?.data?.detail || "Failed to export CSV");
        },
    });

    const { data, isLoading, refetch } = useQuery({
        queryKey: ["transcript", id],
        queryFn: async () => {
            const response = await api.getTranscript(id);
            return response.data.data;
        },
        enabled: !!id,
        // Auto-update status until analysis finishes
        refetchInterval: (query) => {
            const status = query.state.data?.status as TranscriptStatus | undefined;
            if (
                status === TranscriptStatus.UPLOADED ||
                status === TranscriptStatus.ANALYZING
            ) {
                return 1000;
            }
            return false;
        },
        refetchIntervalInBackground: true,
    });

    const { data: tasksData } = useQuery({
        queryKey: ["tasks", { transcript_id: id }],
        queryFn: async () => {
            const response = await api.getTasks({ transcript_id: id });
            return response.data;
        },
        enabled: !!data && data.status === TranscriptStatus.ANALYZED,
    });

    if (isLoading) {
        return <Loading text="Loading transcript..." />;
    }

    if (!data) {
        return <div>Transcript not found</div>;
    }

    const tasks = tasksData?.data || [];

    return (
        <div>
            <PageHeader
                title={data.filename}
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Transcripts", href: "/transcripts" },
                    { label: data.filename },
                ]}
                actions={
                    <div className="flex gap-2">
                        {data.status === TranscriptStatus.ANALYZED && (
                            <>
                                <Link href={`/graph/${id}`}>
                                    <Button variant="outline">
                                        <GitBranch className="h-4 w-4 mr-2" />
                                        View Graph
                                    </Button>
                                </Link>
                                <Button
                                    variant="outline"
                                    onClick={() => exportCsvMutation.mutate()}
                                    disabled={exportCsvMutation.isPending}
                                >
                                    <Download className="h-4 w-4 mr-2" />
                                    {exportCsvMutation.isPending ? "Downloading..." : "Export CSV"}
                                </Button>
                            </>
                        )}
                        <Button variant="ghost" onClick={() => refetch()}>
                            <RefreshCw className="h-4 w-4" />
                        </Button>
                    </div>
                }
            />

            <div className="grid lg:grid-cols-3 gap-6">
                {/* Details */}
                <Card className="lg:col-span-1">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <FileText className="h-5 w-5" />
                            Details
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <p className="text-sm text-muted-foreground">Status</p>
                            <Badge
                                variant={
                                    data.status === TranscriptStatus.ANALYZED
                                        ? "default"
                                        : data.status === TranscriptStatus.FAILED
                                            ? "destructive"
                                            : "secondary"
                                }
                            >
                                {data.status}
                            </Badge>
                        </div>

                        <Separator />

                        <div>
                            <p className="text-sm text-muted-foreground">File Type</p>
                            <p className="font-medium">{data.file_type.toUpperCase()}</p>
                        </div>

                        <div>
                            <p className="text-sm text-muted-foreground">Size</p>
                            <p className="font-medium">
                                {(data.size_bytes / 1024).toFixed(1)} KB
                            </p>
                        </div>

                        <div>
                            <p className="text-sm text-muted-foreground">Uploaded</p>
                            <p className="font-medium">
                                {format(parseISO(data.created_at), "PPP")}
                            </p>
                            <p className="text-sm text-muted-foreground">
                                {formatDistanceToNow(parseISO(data.created_at), {
                                    addSuffix: true,
                                })}
                            </p>
                        </div>

                        {data.status === TranscriptStatus.ANALYZED && (
                            <>
                                <Separator />
                                <div>
                                    <p className="text-sm text-muted-foreground">Tasks Extracted</p>
                                    <p className="text-2xl font-bold">{tasks.length}</p>
                                </div>
                            </>
                        )}

                        {data.error_message && (
                            <>
                                <Separator />
                                <div>
                                    <p className="text-sm text-destructive font-medium">Error</p>
                                    <p className="text-sm text-muted-foreground">
                                        {data.error_message}
                                    </p>
                                </div>
                            </>
                        )}
                    </CardContent>
                </Card>

                {/* Tasks */}
                <Card className="lg:col-span-2">
                    <CardHeader>
                        <CardTitle>Extracted Tasks</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {tasks.length > 0 ? (
                            <div className="space-y-4">
                                {tasks.map((task: any) => (
                                    <TaskCard key={task.id} task={task} />
                                ))}
                            </div>
                        ) : data.status === TranscriptStatus.ANALYZED ? (
                            <p className="text-muted-foreground text-center py-8">
                                No tasks were extracted from this transcript.
                            </p>
                        ) : (
                            <p className="text-muted-foreground text-center py-8">
                                Run analysis to extract tasks from this transcript.
                            </p>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
