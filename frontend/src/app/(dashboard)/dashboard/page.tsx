"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/common";
import { MetricCard } from "@/components/analytics";
import { TranscriptCard } from "@/components/transcript";
import { TaskCard } from "@/components/task";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    FileText,
    ListTodo,
    GitBranch,
    Clock,
    Upload,
    ArrowRight,
} from "lucide-react";
import { Transcript, Task } from "@/types";

export default function DashboardPage() {
    // Fetch analytics
    const { data: analytics, isLoading: analyticsLoading } = useQuery({
        queryKey: ["analytics", "dashboard"],
        queryFn: async () => {
            const response = await api.getDashboardAnalytics();
            return response.data.data;
        },
    });

    // Fetch recent transcripts
    const { data: transcriptsData } = useQuery({
        queryKey: ["transcripts", { page: 1, page_size: 4 }],
        queryFn: async () => {
            const response = await api.getTranscripts({ page: 1, page_size: 4 });
            return response.data;
        },
    });

    // Fetch recent tasks
    const { data: tasksData } = useQuery({
        queryKey: ["tasks", { page: 1, page_size: 4 }],
        queryFn: async () => {
            const response = await api.getTasks({ page: 1, page_size: 4 });
            return response.data;
        },
    });

    const transcripts: Transcript[] = transcriptsData?.data || [];
    const tasks: Task[] = tasksData?.data || [];

    return (
        <div>
            <PageHeader
                title="Dashboard"
                description="Overview of your project analysis"
                actions={
                    <Link href="/upload">
                        <Button>
                            <Upload className="h-4 w-4 mr-2" />
                            Upload Transcript
                        </Button>
                    </Link>
                }
            />

            {/* Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <MetricCard
                    title="Total Transcripts"
                    value={analytics?.transcripts?.total || 0}
                    icon={FileText}
                    description="Uploaded transcripts"
                />
                <MetricCard
                    title="Total Tasks"
                    value={analytics?.tasks?.total || 0}
                    icon={ListTodo}
                    description="Extracted tasks"
                />
                <MetricCard
                    title="Dependencies"
                    value={analytics?.dependencies?.total || 0}
                    icon={GitBranch}
                    description="Task relationships"
                />
                <MetricCard
                    title="Avg Critical Path"
                    value={`${analytics?.metrics?.average_critical_path_hours?.toFixed(1) || 0}h`}
                    icon={Clock}
                    description="Average duration"
                />
            </div>

            {/* Recent Items */}
            <div className="grid lg:grid-cols-2 gap-8">
                {/* Recent Transcripts */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Recent Transcripts</CardTitle>
                        <Link href="/transcripts">
                            <Button variant="ghost" size="sm">
                                View All <ArrowRight className="h-4 w-4 ml-1" />
                            </Button>
                        </Link>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {transcripts.length > 0 ? (
                            transcripts.map((transcript) => (
                                <TranscriptCard key={transcript.id} transcript={transcript} />
                            ))
                        ) : (
                            <p className="text-muted-foreground text-center py-8">
                                No transcripts yet. Upload one to get started!
                            </p>
                        )}
                    </CardContent>
                </Card>

                {/* Recent Tasks */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Recent Tasks</CardTitle>
                        <Link href="/tasks">
                            <Button variant="ghost" size="sm">
                                View All <ArrowRight className="h-4 w-4 ml-1" />
                            </Button>
                        </Link>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {tasks.length > 0 ? (
                            tasks.map((task) => <TaskCard key={task.id} task={task} />)
                        ) : (
                            <p className="text-muted-foreground text-center py-8">
                                No tasks yet. Upload and analyze a transcript!
                            </p>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
