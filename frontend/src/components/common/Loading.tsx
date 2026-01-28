"use client";

import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SpinnerProps {
    size?: "sm" | "md" | "lg";
    className?: string;
}

const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8",
};

export function Spinner({ size = "md", className }: SpinnerProps) {
    return (
        <Loader2
            className={cn("animate-spin text-primary", sizeClasses[size], className)}
        />
    );
}

interface LoadingProps {
    text?: string;
    fullScreen?: boolean;
}

export function Loading({ text = "Loading...", fullScreen = false }: LoadingProps) {
    const content = (
        <div className="flex flex-col items-center justify-center gap-3">
            <Spinner size="lg" />
            <p className="text-sm text-muted-foreground">{text}</p>
        </div>
    );

    if (fullScreen) {
        return (
            <div className="fixed inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm z-50">
                {content}
            </div>
        );
    }

    return (
        <div className="flex items-center justify-center p-8">{content}</div>
    );
}
