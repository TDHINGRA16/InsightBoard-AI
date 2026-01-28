"use client";

import { useAuth } from "@/hooks";
import { redirect } from "next/navigation";
import { Sidebar, Header } from "@/components/layout";
import { Loading } from "@/components/common";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { session, loading } = useAuth();

    if (loading) {
        return <Loading fullScreen text="Loading..." />;
    }

    if (!session) {
        redirect("/login");
    }

    return (
        <div className="flex h-screen bg-background">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
                <Header />
                <main className="flex-1 overflow-auto p-6">{children}</main>
            </div>
        </div>
    );
}
