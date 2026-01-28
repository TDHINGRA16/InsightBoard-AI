"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { PageHeader } from "@/components/common";
import { FileUpload, AnalysisProgress } from "@/components/transcript";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";
import { Play, GitBranch } from "lucide-react";

export default function UploadPage() {
    const router = useRouter();
    const [uploadedTranscriptId, setUploadedTranscriptId] = useState<string | null>(
        null
    );
    const [jobId, setJobId] = useState<string | null>(null);

    // Start analysis mutation
    const startAnalysisMutation = useMutation({
        mutationFn: async (transcriptId: string) => {
            // Always use force=true to regenerate tasks if re-submitted
            const response = await api.startAnalysis(transcriptId, { force: true });
            return response.data;
        },
        onSuccess: (data) => {
            setJobId(data.data.job_id);
            toast.success("Analysis started!");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to start analysis");
        },
    });

    const handleUploadSuccess = (transcriptId: string) => {
        setUploadedTranscriptId(transcriptId);
    };

    const handleStartAnalysis = () => {
        if (uploadedTranscriptId) {
            startAnalysisMutation.mutate(uploadedTranscriptId);
        }
    };

    const handleAnalysisComplete = (result: any) => {
        toast.success("Analysis complete! Tasks and dependencies extracted.");
        // Navigate to the transcript details
        setTimeout(() => {
            router.push(`/transcripts/${uploadedTranscriptId}`);
        }, 1500);
    };

    return (
        <div className="max-w-3xl mx-auto">
            <PageHeader
                title="Upload Transcript"
                description="Upload a project transcript to analyze and extract task dependencies"
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Upload" },
                ]}
            />

            {/* File Upload */}
            <Card className="mb-8">
                <CardHeader>
                    <CardTitle>Upload File</CardTitle>
                </CardHeader>
                <CardContent>
                    <FileUpload onUploadSuccess={handleUploadSuccess} />
                </CardContent>
            </Card>

            {/* Start Analysis */}
            {uploadedTranscriptId && !jobId && (
                <Card className="mb-8">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <GitBranch className="h-5 w-5" />
                            Ready for Analysis
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-muted-foreground mb-4">
                            Your transcript has been uploaded. Start the AI analysis to extract
                            tasks and dependencies automatically.
                        </p>
                        <Button
                            onClick={handleStartAnalysis}
                            disabled={startAnalysisMutation.isPending}
                        >
                            <Play className="h-4 w-4 mr-2" />
                            {startAnalysisMutation.isPending ? "Starting..." : "Start Analysis"}
                        </Button>
                    </CardContent>
                </Card>
            )}

            {/* Analysis Progress */}
            {jobId && (
                <AnalysisProgress
                    jobId={jobId}
                    onComplete={handleAnalysisComplete}
                    onError={(error) => toast.error(error)}
                />
            )}
        </div>
    );
}
