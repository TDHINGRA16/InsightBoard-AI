"use client";

import { ReactNode } from "react";
import { FileQuestion, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
    icon?: ReactNode;
    title: string;
    description: string;
    actionLabel?: string;
    onAction?: () => void;
}

export function EmptyState({
    icon,
    title,
    description,
    actionLabel,
    onAction,
}: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center p-12 text-center">
            <div className="rounded-full bg-muted p-4 mb-4">
                {icon || <FileQuestion className="h-8 w-8 text-muted-foreground" />}
            </div>
            <h3 className="text-lg font-semibold mb-2">{title}</h3>
            <p className="text-sm text-muted-foreground max-w-sm mb-6">
                {description}
            </p>
            {actionLabel && onAction && (
                <Button onClick={onAction}>
                    <Plus className="h-4 w-4 mr-2" />
                    {actionLabel}
                </Button>
            )}
        </div>
    );
}
