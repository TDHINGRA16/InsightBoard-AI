"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
    title: string;
    value: string | number;
    description?: string;
    icon?: LucideIcon;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    className?: string;
}

export function MetricCard({
    title,
    value,
    description,
    icon: Icon,
    trend,
    className,
}: MetricCardProps) {
    return (
        <Card className={cn("overflow-hidden", className)}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                    {title}
                </CardTitle>
                {Icon && (
                    <div className="rounded-lg bg-primary/10 p-2">
                        <Icon className="h-4 w-4 text-primary" />
                    </div>
                )}
            </CardHeader>
            <CardContent>
                <div className="text-3xl font-bold">{value}</div>
                {description && (
                    <p className="text-sm text-muted-foreground mt-1">{description}</p>
                )}
                {trend && (
                    <div
                        className={cn(
                            "text-sm mt-2 flex items-center gap-1",
                            trend.isPositive ? "text-green-600" : "text-red-600"
                        )}
                    >
                        <span>{trend.isPositive ? "↑" : "↓"}</span>
                        <span>{Math.abs(trend.value)}% from last period</span>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
