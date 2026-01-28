"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import { DependencyGraph, GraphControls, GraphLegend } from "@/components/graph";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Download, ArrowLeft } from "lucide-react";

export default function GraphPage() {
    const { transcriptId } = useParams<{ transcriptId: string }>();

    // Fetch graph visualization data
    const { data: graphData, isLoading: graphLoading } = useQuery({
        queryKey: ["graph", "visualization", transcriptId],
        queryFn: async () => {
            const response = await api.getGraphVisualization(transcriptId);
            // Backend returns { success, data: { nodes, edges }, metrics, transcript_id }
            return response.data?.data || { nodes: [], edges: [] };
        },
    });

    // Fetch critical path
    const { data: criticalPathData } = useQuery({
        queryKey: ["graph", "critical-path", transcriptId],
        queryFn: async () => {
            const response = await api.getCriticalPath(transcriptId);
            // Returns { success, critical_path: [...], ... } - no nested data
            return response.data || { critical_path: [] };
        },
    });

    // Fetch transcript info
    const { data: transcriptData } = useQuery({
        queryKey: ["transcript", transcriptId],
        queryFn: async () => {
            const response = await api.getTranscript(transcriptId);
            return response.data.data;
        },
    });

    if (graphLoading) {
        return <Loading text="Loading graph..." />;
    }

    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh]">
                <p className="text-muted-foreground mb-4">
                    No graph data available for this transcript.
                </p>
                <Link href={`/transcripts/${transcriptId}`}>
                    <Button variant="outline">
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Back to Transcript
                    </Button>
                </Link>
            </div>
        );
    }

    const criticalPath = criticalPathData?.critical_path || [];

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col">
            <PageHeader
                title="Dependency Graph"
                description={transcriptData?.filename || "Visualization"}
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Transcripts", href: "/transcripts" },
                    { label: transcriptData?.filename || "Transcript", href: `/transcripts/${transcriptId}` },
                    { label: "Graph" },
                ]}
                actions={
                    <Link href={`/export?transcript_id=${transcriptId}`}>
                        <Button variant="outline">
                            <Download className="h-4 w-4 mr-2" />
                            Export
                        </Button>
                    </Link>
                }
            />

            <div className="flex gap-4 flex-1 min-h-0">
                {/* Main Graph */}
                <div className="flex-1 flex flex-col">
                    <div className="mb-4">
                        <GraphControls />
                    </div>
                    <div className="flex-1 border rounded-lg overflow-hidden">
                        <DependencyGraph
                            graphData={graphData}
                            criticalPath={criticalPath}
                        />
                    </div>
                </div>

                {/* Sidebar */}
                <div className="w-64 space-y-4">
                    {/* Legend */}
                    <GraphLegend />

                    {/* Critical Path Info */}
                    {criticalPathData && criticalPath.length > 0 && (
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm">Critical Path</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-2xl font-bold">
                                    {criticalPathData.total_duration_hours?.toFixed(1)}h
                                </p>
                                <p className="text-sm text-muted-foreground">
                                    {criticalPath.length} tasks in critical path
                                </p>
                                <p className="text-sm text-muted-foreground mt-1">
                                    ~{criticalPathData.total_duration_days?.toFixed(1)} days
                                </p>
                            </CardContent>
                        </Card>
                    )}

                    {/* Graph Stats */}
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm">Statistics</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            <div className="flex justify-between">
                                <span className="text-sm text-muted-foreground">Nodes</span>
                                <span className="font-medium">{graphData.nodes.length}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-sm text-muted-foreground">Edges</span>
                                <span className="font-medium">{graphData.edges.length}</span>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
