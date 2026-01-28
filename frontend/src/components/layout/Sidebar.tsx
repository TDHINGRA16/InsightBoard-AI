"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Upload,
    FileText,
    ListTodo,
    GitBranch,
    BarChart3,
    Download,
    Webhook,
    Settings,
    ChevronLeft,
    ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store";
import { Button } from "@/components/ui/button";

const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/upload", label: "Upload", icon: Upload },
    { href: "/transcripts", label: "Transcripts", icon: FileText },
    { href: "/tasks", label: "Tasks", icon: ListTodo },
    { href: "/dependencies", label: "Dependencies", icon: GitBranch },
    { href: "/analytics", label: "Analytics", icon: BarChart3 },
    { href: "/export", label: "Export", icon: Download },
    { href: "/webhooks", label: "Webhooks", icon: Webhook },
];

export default function Sidebar() {
    const pathname = usePathname();
    const { sidebarOpen, toggleSidebar } = useUIStore();

    return (
        <aside
            className={cn(
                "relative flex flex-col bg-card border-r transition-all duration-300",
                sidebarOpen ? "w-64" : "w-16"
            )}
        >
            {/* Logo */}
            <div className="flex items-center h-16 px-4 border-b">
                {sidebarOpen ? (
                    <Link href="/dashboard" className="flex items-center gap-2">
                        <GitBranch className="h-8 w-8 text-primary" />
                        <span className="font-bold text-lg">InsightBoard</span>
                    </Link>
                ) : (
                    <Link href="/dashboard">
                        <GitBranch className="h-8 w-8 text-primary mx-auto" />
                    </Link>
                )}
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-2">
                {navItems.map((item) => {
                    const isActive = pathname.startsWith(item.href);
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                                isActive
                                    ? "bg-primary text-primary-foreground"
                                    : "hover:bg-muted text-muted-foreground hover:text-foreground"
                            )}
                        >
                            <item.icon className="h-5 w-5 flex-shrink-0" />
                            {sidebarOpen && <span>{item.label}</span>}
                        </Link>
                    );
                })}
            </nav>

            {/* Settings */}
            <div className="p-4 border-t">
                <Link
                    href="/settings"
                    className={cn(
                        "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                        "hover:bg-muted text-muted-foreground hover:text-foreground"
                    )}
                >
                    <Settings className="h-5 w-5 flex-shrink-0" />
                    {sidebarOpen && <span>Settings</span>}
                </Link>
            </div>

            {/* Toggle Button */}
            <Button
                variant="ghost"
                size="icon"
                onClick={toggleSidebar}
                className="absolute -right-3 top-20 h-6 w-6 rounded-full border bg-background"
            >
                {sidebarOpen ? (
                    <ChevronLeft className="h-4 w-4" />
                ) : (
                    <ChevronRight className="h-4 w-4" />
                )}
            </Button>
        </aside>
    );
}
