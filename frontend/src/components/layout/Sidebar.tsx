"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    FileText,
    CheckSquare,
    GitBranch,
    Sparkles,
} from "lucide-react";

import { cn } from "@/lib/utils";

const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/transcripts", label: "Transcripts", icon: FileText },
    { href: "/tasks", label: "Tasks", icon: CheckSquare },
    { href: "/graphs", label: "Dependencies", icon: GitBranch },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="w-56 border-r bg-background flex flex-col h-screen">
            {/* Logo */}
            <div className="px-4 py-5 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <span className="text-base font-semibold tracking-tight">Explore</span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-2 space-y-0.5">
                {navItems.map((item) => {
                    const active = pathname === item.href || pathname?.startsWith(item.href + "/");
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                                active
                                    ? "bg-primary/10 text-primary font-medium"
                                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                            )}
                        >
                            <Icon className="h-4 w-4 shrink-0" />
                            <span>{item.label}</span>
                        </Link>
                    );
                })}
            </nav>
        </aside>
    );
}



