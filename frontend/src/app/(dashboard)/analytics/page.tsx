"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import { MetricCard } from "@/components/analytics";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    FileText,
    ListTodo,
    GitBranch,
    Clock,
    CheckCircle,
    AlertTriangle,
    Loader2,
    XCircle,
} from "lucide-react";

export default function AnalyticsPage() {
    const { data: analytics, isLoading } = useQuery({
        queryKey: ["analytics", "dashboard"],
        queryFn: async () => {
            const response = await api.getDashboardAnalytics();
            return response.data.data;
        },
    });

    if (isLoading) {
        return <Loading text="Loading analytics..." />;
    }

    return (
        <div>
            <PageHeader
                title="Analytics"
                description="Overview of your project metrics"
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Analytics" },
                ]}
            />

            {/* Main Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <MetricCard
                    title="Total Transcripts"
                    value={analytics?.transcripts?.total || 0}
                    icon={FileText}
                />
                <MetricCard
                    title="Total Tasks"
                    value={analytics?.tasks?.total || 0}
                    icon={ListTodo}
                />
                <MetricCard
                    title="Total Dependencies"
                    value={analytics?.dependencies?.total || 0}
                    icon={GitBranch}
                />
                <MetricCard
                    title="Avg Critical Path"
                    value={`${analytics?.metrics?.average_critical_path_hours?.toFixed(1) || 0}h`}
                    icon={Clock}
                />
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
                {/* Tasks by Status */}
                <Card>
                    <CardHeader>
                        <CardTitle>Tasks by Status</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <StatusRow
                                icon={Clock}
                                label="Pending"
                                value={analytics?.tasks?.by_status?.pending || 0}
                                color="text-slate-500"
                            />
                            <StatusRow
                                icon={Loader2}
                                label="In Progress"
                                value={analytics?.tasks?.by_status?.in_progress || 0}
                                color="text-blue-500"
                            />
                            <StatusRow
                                icon={CheckCircle}
                                label="Completed"
                                value={analytics?.tasks?.by_status?.completed || 0}
                                color="text-green-500"
                            />
                            <StatusRow
                                icon={XCircle}
                                label="Blocked"
                                value={analytics?.tasks?.by_status?.blocked || 0}
                                color="text-red-500"
                            />
                        </div>
                    </CardContent>
                </Card>

                {/* Tasks by Priority */}
                <Card>
                    <CardHeader>
                        <CardTitle>Tasks by Priority</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <PriorityRow
                                label="Critical"
                                value={analytics?.tasks?.by_priority?.critical || 0}
                                color="bg-red-500"
                            />
                            <PriorityRow
                                label="High"
                                value={analytics?.tasks?.by_priority?.high || 0}
                                color="bg-orange-500"
                            />
                            <PriorityRow
                                label="Medium"
                                value={analytics?.tasks?.by_priority?.medium || 0}
                                color="bg-yellow-500"
                            />
                            <PriorityRow
                                label="Low"
                                value={analytics?.tasks?.by_priority?.low || 0}
                                color="bg-gray-400"
                            />
                        </div>
                    </CardContent>
                </Card>

                {/* Transcripts by Status */}
                <Card>
                    <CardHeader>
                        <CardTitle>Transcripts by Status</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <StatusRow
                                icon={FileText}
                                label="Uploaded"
                                value={analytics?.transcripts?.by_status?.uploaded || 0}
                                color="text-blue-500"
                            />
                            <StatusRow
                                icon={Loader2}
                                label="Analyzing"
                                value={analytics?.transcripts?.by_status?.analyzing || 0}
                                color="text-yellow-500"
                            />
                            <StatusRow
                                icon={CheckCircle}
                                label="Analyzed"
                                value={analytics?.transcripts?.by_status?.analyzed || 0}
                                color="text-green-500"
                            />
                            <StatusRow
                                icon={AlertTriangle}
                                label="Failed"
                                value={analytics?.transcripts?.by_status?.failed || 0}
                                color="text-red-500"
                            />
                        </div>
                    </CardContent>
                </Card>

                {/* Jobs Overview */}
                <Card>
                    <CardHeader>
                        <CardTitle>Jobs Overview</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <StatusRow
                                icon={Clock}
                                label="Queued"
                                value={analytics?.jobs?.by_status?.queued || 0}
                                color="text-slate-500"
                            />
                            <StatusRow
                                icon={Loader2}
                                label="Processing"
                                value={analytics?.jobs?.by_status?.processing || 0}
                                color="text-blue-500"
                            />
                            <StatusRow
                                icon={CheckCircle}
                                label="Completed"
                                value={analytics?.jobs?.by_status?.completed || 0}
                                color="text-green-500"
                            />
                            <StatusRow
                                icon={XCircle}
                                label="Failed"
                                value={analytics?.jobs?.by_status?.failed || 0}
                                color="text-red-500"
                            />
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

function StatusRow({
    icon: Icon,
    label,
    value,
    color,
}: {
    icon: any;
    label: string;
    value: number;
    color: string;
}) {
    return (
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
                <Icon className={`h-4 w-4 ${color}`} />
                <span className="text-sm">{label}</span>
            </div>
            <span className="font-semibold">{value}</span>
        </div>
    );
}

function PriorityRow({
    label,
    value,
    color,
}: {
    label: string;
    value: number;
    color: string;
}) {
    const total = 100; // Placeholder for percentage calculation
    const percentage = total > 0 ? (value / total) * 100 : 0;

    return (
        <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
                <span>{label}</span>
                <span className="font-semibold">{value}</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                    className={`h-full ${color} transition-all`}
                    style={{ width: `${Math.min(percentage, 100)}%` }}
                />
            </div>
        </div>
    );
}
