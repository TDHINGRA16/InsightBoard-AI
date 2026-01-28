"use client";

import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { FileText, MoreVertical, Eye, Trash2, Play, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Transcript, TranscriptStatus } from "@/types";
import { cn } from "@/lib/utils";

interface TranscriptCardProps {
    transcript: Transcript;
    onDelete?: (id: string) => void;
    onAnalyze?: (id: string) => void;
    onReanalyze?: (id: string) => void;
}

const statusColors: Record<TranscriptStatus, string> = {
    [TranscriptStatus.UPLOADED]: "bg-blue-100 text-blue-800",
    [TranscriptStatus.ANALYZING]: "bg-yellow-100 text-yellow-800",
    [TranscriptStatus.ANALYZED]: "bg-green-100 text-green-800",
    [TranscriptStatus.FAILED]: "bg-red-100 text-red-800",
};

const statusLabels: Record<TranscriptStatus, string> = {
    [TranscriptStatus.UPLOADED]: "Uploaded",
    [TranscriptStatus.ANALYZING]: "Analyzing...",
    [TranscriptStatus.ANALYZED]: "Analyzed",
    [TranscriptStatus.FAILED]: "Failed",
};

export function TranscriptCard({
    transcript,
    onDelete,
    onAnalyze,
    onReanalyze,
}: TranscriptCardProps) {
    const canAnalyze =
        transcript.status === TranscriptStatus.UPLOADED ||
        transcript.status === TranscriptStatus.FAILED;

    const canReanalyze = transcript.status === TranscriptStatus.ANALYZED;

    return (
        <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-start justify-between pb-2">
                <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-primary/10 p-2">
                        <FileText className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                        <Link
                            href={`/transcripts/${transcript.id}`}
                            className="font-semibold hover:text-primary transition-colors"
                        >
                            {transcript.filename}
                        </Link>
                        <p className="text-sm text-muted-foreground">
                            {formatDistanceToNow(new Date(transcript.created_at), {
                                addSuffix: true,
                            })}
                        </p>
                    </div>
                </div>

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuItem asChild>
                            <Link href={`/transcripts/${transcript.id}`}>
                                <Eye className="h-4 w-4 mr-2" />
                                View Details
                            </Link>
                        </DropdownMenuItem>
                        {canAnalyze && onAnalyze && (
                            <DropdownMenuItem onClick={() => onAnalyze(transcript.id)}>
                                <Play className="h-4 w-4 mr-2" />
                                Start Analysis
                            </DropdownMenuItem>
                        )}
                        {canReanalyze && onReanalyze && (
                            <DropdownMenuItem onClick={() => onReanalyze(transcript.id)}>
                                <RefreshCw className="h-4 w-4 mr-2" />
                                Re-analyze
                            </DropdownMenuItem>
                        )}
                        {onDelete && (
                            <DropdownMenuItem
                                onClick={() => onDelete(transcript.id)}
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
                <div className="flex items-center justify-between">
                    <Badge className={cn("font-medium", statusColors[transcript.status])}>
                        {statusLabels[transcript.status]}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                        {(transcript.size_bytes / 1024).toFixed(1)} KB
                    </span>
                </div>

                {transcript.status === TranscriptStatus.ANALYZED && transcript.tasks && (
                    <p className="text-sm text-muted-foreground mt-2">
                        {transcript.tasks.length} tasks extracted
                    </p>
                )}

                {transcript.status === TranscriptStatus.FAILED && transcript.error_message && (
                    <p className="text-sm text-destructive mt-2">
                        {transcript.error_message}
                    </p>
                )}
            </CardContent>
        </Card>
    );
}
