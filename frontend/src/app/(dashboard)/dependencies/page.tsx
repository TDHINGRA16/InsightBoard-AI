"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader, EmptyState, Loading } from "@/components/common";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GitBranch, ArrowRight } from "lucide-react";
import { Dependency, DependencyType } from "@/types";
import Link from "next/link";

export default function DependenciesPage() {
    const { data, isLoading } = useQuery({
        queryKey: ["dependencies"],
        queryFn: async () => {
            const response = await api.getDependencies({});
            return response.data;
        },
    });

    const dependencies: Dependency[] = data?.data || [];

    if (isLoading) {
        return <Loading text="Loading dependencies..." />;
    }

    return (
        <div>
            <PageHeader
                title="Dependencies"
                description="View all task dependencies across your projects"
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Dependencies" },
                ]}
            />

            {dependencies.length === 0 ? (
                <EmptyState
                    icon={<GitBranch className="h-8 w-8 text-muted-foreground" />}
                    title="No dependencies yet"
                    description="Dependencies will appear here after you analyze transcripts with related tasks."
                />
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {dependencies.map((dep) => (
                        <DependencyCard key={dep.id} dependency={dep} />
                    ))}
                </div>
            )}
        </div>
    );
}

function DependencyCard({ dependency }: { dependency: Dependency }) {
    const typeColors: Record<DependencyType, string> = {
        [DependencyType.BLOCKS]: "bg-red-100 text-red-800",
        [DependencyType.PRECEDES]: "bg-blue-100 text-blue-800",
        [DependencyType.PARENT_OF]: "bg-purple-100 text-purple-800",
        [DependencyType.RELATED_TO]: "bg-gray-100 text-gray-800",
    };

    return (
        <Card>
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <Badge className={typeColors[dependency.dependency_type]}>
                        {dependency.dependency_type.replace("_", " ")}
                    </Badge>
                    {dependency.lag_days > 0 && (
                        <span className="text-sm text-muted-foreground">
                            +{dependency.lag_days} days lag
                        </span>
                    )}
                </div>
            </CardHeader>
            <CardContent>
                <div className="flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                        <Link
                            href={`/tasks/${dependency.depends_on_task_id}`}
                            className="block text-sm font-medium hover:text-primary truncate"
                        >
                            {dependency.depends_on_task?.title ||
                                dependency.depends_on_title ||
                                "Task"}
                        </Link>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="flex-1 min-w-0">
                        <Link
                            href={`/tasks/${dependency.task_id}`}
                            className="block text-sm font-medium hover:text-primary truncate"
                        >
                            {dependency.task?.title ||
                                dependency.task_title ||
                                "Task"}
                        </Link>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
