"use client";

import type { ComponentType } from "react";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Download, FileSpreadsheet } from "lucide-react";
import { toast } from "sonner";

export default function ExportPage() {
    const searchParams = useSearchParams();
    const preselectedTranscriptId = searchParams.get("transcript_id");

    const [selectedTranscript, setSelectedTranscript] = useState<string>(
        preselectedTranscriptId || ""
    );

    // Fetch transcripts
    const { data: transcriptsData, isLoading: transcriptsLoading } = useQuery({
        queryKey: ["transcripts"],
        queryFn: async () => {
            const response = await api.getTranscripts();
            return response.data;
        },
    });

    // Export mutations
    const exportCsvMutation = useMutation({
        mutationFn: async (transcriptId: string) => {
            const response = await api.exportCsv(transcriptId);
            return response.data;
        },
        onSuccess: (data) => {
            // Download as CSV file
            const url = window.URL.createObjectURL(data as Blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `export-${selectedTranscript}.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
            toast.success("CSV exported successfully!");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Export failed");
        },
    });

    const transcripts = transcriptsData?.data || [];
    const isExporting = exportCsvMutation.isPending;

    const handleExport = () => {
        if (!selectedTranscript) {
            toast.error("Please select a transcript");
            return;
        }

        exportCsvMutation.mutate(selectedTranscript);
    };

    if (transcriptsLoading) {
        return <Loading text="Loading..." />;
    }

    return (
        <div className="max-w-2xl mx-auto">
            <PageHeader
                title="Export"
                description="Export your workflow data in various formats"
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Export" },
                ]}
            />

            <Card>
                <CardHeader>
                    <CardTitle>Export Options</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Transcript Selection */}
                    <div>
                        <label className="block text-sm font-medium mb-2">
                            Select Transcript
                        </label>
                        <Select
                            value={selectedTranscript}
                            onValueChange={setSelectedTranscript}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Choose a transcript..." />
                            </SelectTrigger>
                            <SelectContent>
                                {transcripts.map((t: any) => (
                                    <SelectItem key={t.id} value={t.id}>
                                        {t.filename}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Format Selection */}
                    <div>
                        <label className="block text-sm font-medium mb-2">
                            Export Format
                        </label>
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            <FormatCard
                                icon={FileSpreadsheet}
                                label="CSV"
                                description="Spreadsheet compatible"
                                selected
                                onClick={() => {}}
                            />
                        </div>
                    </div>

                    {/* Export Button */}
                    <Button
                        className="w-full"
                        onClick={handleExport}
                        disabled={!selectedTranscript || isExporting}
                    >
                        <Download className="h-4 w-4 mr-2" />
                        {isExporting ? "Exporting..." : "Export Data"}
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}

function FormatCard({
    icon: Icon,
    label,
    description,
    selected,
    onClick,
}: {
    icon: ComponentType<{ className?: string }>;
    label: string;
    description: string;
    selected: boolean;
    onClick: () => void;
}) {
    return (
        <button
            onClick={onClick}
            className={`p-4 rounded-lg border-2 text-left transition-all ${selected
                    ? "border-primary bg-primary/5"
                    : "border-muted hover:border-primary/50"
                }`}
        >
            <Icon className={`h-6 w-6 mb-2 ${selected ? "text-primary" : ""}`} />
            <p className="font-medium">{label}</p>
            <p className="text-xs text-muted-foreground">{description}</p>
        </button>
    );
}
