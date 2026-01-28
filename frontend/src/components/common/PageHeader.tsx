"use client";

import { ReactNode } from "react";
import { ChevronRight } from "lucide-react";
import Link from "next/link";

interface Breadcrumb {
    label: string;
    href?: string;
}

interface PageHeaderProps {
    title: string;
    description?: string;
    breadcrumbs?: Breadcrumb[];
    actions?: ReactNode;
}

export function PageHeader({
    title,
    description,
    breadcrumbs,
    actions,
}: PageHeaderProps) {
    return (
        <div className="mb-8">
            {/* Breadcrumbs */}
            {breadcrumbs && breadcrumbs.length > 0 && (
                <nav className="flex items-center gap-1 text-sm text-muted-foreground mb-2">
                    {breadcrumbs.map((crumb, index) => (
                        <span key={index} className="flex items-center gap-1">
                            {index > 0 && <ChevronRight className="h-4 w-4" />}
                            {crumb.href ? (
                                <Link
                                    href={crumb.href}
                                    className="hover:text-foreground transition-colors"
                                >
                                    {crumb.label}
                                </Link>
                            ) : (
                                <span className="text-foreground">{crumb.label}</span>
                            )}
                        </span>
                    ))}
                </nav>
            )}

            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
                    {description && (
                        <p className="text-muted-foreground mt-1">{description}</p>
                    )}
                </div>
                {actions && <div className="flex items-center gap-2">{actions}</div>}
            </div>
        </div>
    );
}
