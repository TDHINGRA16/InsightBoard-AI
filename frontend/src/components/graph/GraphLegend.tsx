"use client";

import { Card } from "@/components/ui/card";

export function GraphLegend() {
    const items = [
        { color: "bg-red-500", label: "Critical Path" },
        { color: "bg-blue-400", label: "In Progress" },
        { color: "bg-green-400", label: "Completed" },
        { color: "bg-slate-300", label: "Pending" },
        { color: "bg-red-400", label: "Blocked" },
    ];

    const priorities = [
        { color: "bg-gray-100 border-gray-300", label: "Low" },
        { color: "bg-yellow-100 border-yellow-300", label: "Medium" },
        { color: "bg-orange-100 border-orange-300", label: "High" },
        { color: "bg-red-100 border-red-300", label: "Critical" },
    ];

    return (
        <Card className="p-4">
            <h4 className="font-semibold text-sm mb-3">Legend</h4>

            {/* Status */}
            <div className="space-y-2 mb-4">
                <p className="text-xs text-muted-foreground font-medium">Status</p>
                {items.map((item) => (
                    <div key={item.label} className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded ${item.color}`} />
                        <span className="text-sm">{item.label}</span>
                    </div>
                ))}
            </div>

            {/* Priority */}
            <div className="space-y-2">
                <p className="text-xs text-muted-foreground font-medium">Priority</p>
                {priorities.map((item) => (
                    <div key={item.label} className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded border ${item.color}`} />
                        <span className="text-sm">{item.label}</span>
                    </div>
                ))}
            </div>
        </Card>
    );
}
