"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import { LiveDependencyGraph } from "@/components/graph";
import { GraphControls, GraphLegend } from "@/components/graph";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Link from "next/link";
import {
    Download,
    ArrowLeft,
    Activity,
    Zap,
    GitBranch,
    BarChart3,
} from "lucide-react";

/**
 * Live Dependency Graph page with real-time task updates and interactivity.
 */
export default function LiveGraphPage() {
    const { transcriptId } = useParams<{ transcriptId: string }>();

    // Fetch transcript info
    const { data: transcriptData, isLoading } = useQuery({
        queryKey: ["transcript", transcriptId],
        queryFn: async () => {
            const response = await api.getTranscript(transcriptId);
            return response.data.data;
        },
    });

    // Fetch bottlenecks
    const { data: bottlenecksData } = useQuery({
        queryKey: ["graph", "bottlenecks", transcriptId],
        queryFn: async () => {
            const response = await api.getBottlenecks(transcriptId);
            return response.data;
        },
    });

    if (isLoading) {
        return <Loading text="Loading graph..." />;
    }

    const bottlenecks = bottlenecksData?.data || [];

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col">
            <PageHeader
                title="Live Dependency Graph"
                description={transcriptData?.filename || "Visualization"}
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Transcripts", href: "/transcripts" },
                    {
                        label: transcriptData?.filename || "Transcript",
                        href: `/transcripts/${transcriptId}`,
                    },
                    { label: "Live Graph" },
                ]}
                actions={
                    <div className="flex items-center gap-2">
                        <Badge
                            variant="secondary"
                            className="bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                        >
                            <Activity className="h-3 w-3 mr-1" />
                            Live
                        </Badge>
                        <Link href={`/graph/${transcriptId}`}>
                            <Button variant="outline" size="sm">
                                <GitBranch className="h-4 w-4 mr-2" />
                                Static View
                            </Button>
                        </Link>
                        <Link href={`/export?transcript_id=${transcriptId}`}>
                            <Button variant="outline" size="sm">
                                <Download className="h-4 w-4 mr-2" />
                                Export
                            </Button>
                        </Link>
                    </div>
                }
            />

            <div className="flex gap-4 flex-1 min-h-0">
                {/* Main Graph */}
                <div className="flex-1 flex flex-col">
                    <div className="mb-4">
                        <GraphControls />
                    </div>
                    <div className="flex-1 border rounded-lg overflow-hidden">
                        <LiveDependencyGraph transcriptId={transcriptId} />
                    </div>
                </div>

                {/* Sidebar */}
                <div className="w-72 space-y-4 overflow-auto">
                    <Tabs defaultValue="legend" className="w-full">
                        <TabsList className="w-full">
                            <TabsTrigger value="legend" className="flex-1">
                                Legend
                            </TabsTrigger>
                            <TabsTrigger value="bottlenecks" className="flex-1">
                                Bottlenecks
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="legend" className="mt-4">
                            <GraphLegend />
                        </TabsContent>

                        <TabsContent value="bottlenecks" className="mt-4 space-y-3">
                            {bottlenecks.length > 0 ? (
                                bottlenecks.map((bottleneck: any, index: number) => (
                                    <Card key={bottleneck.task_id}>
                                        <CardContent className="p-3">
                                            <div className="flex items-start gap-3">
                                                <div
                                                    className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold ${index === 0
                                                        ? "bg-red-100 text-red-700"
                                                        : index === 1
                                                            ? "bg-orange-100 text-orange-700"
                                                            : "bg-amber-100 text-amber-700"
                                                        }`}
                                                >
                                                    {index + 1}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium line-clamp-1">
                                                        {bottleneck.title}
                                                    </p>
                                                    <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
                                                        <span>In: {bottleneck.in_degree}</span>
                                                        <span>Out: {bottleneck.out_degree}</span>
                                                        <span>Score: {bottleneck.score.toFixed(1)}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))
                            ) : (
                                <Card>
                                    <CardContent className="p-4 text-center text-sm text-muted-foreground">
                                        No bottlenecks detected
                                    </CardContent>
                                </Card>
                            )}
                        </TabsContent>
                    </Tabs>

                    {/* Info Card */}
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm flex items-center gap-2">
                                <Zap className="h-4 w-4" />
                                Live Features
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="text-xs text-muted-foreground space-y-2">
                            <p>• Real-time task status updates</p>
                            <p>• Click tasks to view details</p>
                            <p>• Start/complete tasks directly</p>
                            <p>• Auto-refresh on changes</p>
                            <p>• Critical path highlighting</p>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
