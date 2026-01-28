"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { PageHeader, EmptyState, Loading } from "@/components/common";
import { TranscriptCard } from "@/components/transcript";
import { Button } from "@/components/ui/button";
import { Upload, FileText } from "lucide-react";
import { Transcript } from "@/types";
import { toast } from "sonner";

export default function TranscriptsPage() {
    const queryClient = useQueryClient();

    const { data, isLoading } = useQuery({
        queryKey: ["transcripts"],
        queryFn: async () => {
            const response = await api.getTranscripts();
            return response.data;
        },
    });

    const deleteTranscriptMutation = useMutation({
        mutationFn: async (id: string) => {
            await api.deleteTranscript(id);
            return id;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["transcripts"] });
            toast.success("Transcript deleted");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to delete");
        },
    });

    const startAnalysisMutation = useMutation({
        mutationFn: async (id: string) => {
            // Always force to handle idempotency - regenerate tasks if re-submitted
            const response = await api.startAnalysis(id, { force: true });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["transcripts"] });
            toast.success("Analysis started!");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to start analysis");
        },
    });

    const reanalyzeMutation = useMutation({
        mutationFn: async (id: string) => {
            // Use force=true to regenerate tasks even if already analyzed
            const response = await api.startAnalysis(id, { force: true });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["transcripts"] });
            toast.success("Re-analysis started! Old tasks will be replaced.");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to start re-analysis");
        },
    });

    const transcripts: Transcript[] = data?.data || [];

    if (isLoading) {
        return <Loading text="Loading transcripts..." />;
    }

    return (
        <div>
            <PageHeader
                title="Transcripts"
                description="Manage your uploaded project transcripts"
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Transcripts" },
                ]}
                actions={
                    <Link href="/upload">
                        <Button>
                            <Upload className="h-4 w-4 mr-2" />
                            Upload
                        </Button>
                    </Link>
                }
            />

            {transcripts.length === 0 ? (
                <EmptyState
                    icon={<FileText className="h-8 w-8 text-muted-foreground" />}
                    title="No transcripts yet"
                    description="Upload your first project transcript to get started with dependency analysis."
                    actionLabel="Upload Transcript"
                    onAction={() => (window.location.href = "/upload")}
                />
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {transcripts.map((transcript) => (
                        <TranscriptCard
                            key={transcript.id}
                            transcript={transcript}
                            onDelete={(id) => deleteTranscriptMutation.mutate(id)}
                            onAnalyze={(id) => startAnalysisMutation.mutate(id)}
                            onReanalyze={(id) => reanalyzeMutation.mutate(id)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
