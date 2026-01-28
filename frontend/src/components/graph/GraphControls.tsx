"use client";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
    ZoomIn,
    ZoomOut,
    Maximize2,
    Map,
    Route,
    LayoutGrid,
} from "lucide-react";
import { useGraphStore } from "@/store";
import { cn } from "@/lib/utils";

interface GraphControlsProps {
    onFitView?: () => void;
    onZoomIn?: () => void;
    onZoomOut?: () => void;
}

export function GraphControls({
    onFitView,
    onZoomIn,
    onZoomOut,
}: GraphControlsProps) {
    const {
        highlightCriticalPath,
        showMiniMap,
        layoutDirection,
        toggleCriticalPath,
        toggleMiniMap,
        setLayoutDirection,
    } = useGraphStore();

    return (
        <div className="flex items-center gap-2 p-2 bg-card border rounded-lg shadow-sm">
            {/* Zoom Controls */}
            <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" onClick={onZoomIn}>
                    <ZoomIn className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" onClick={onZoomOut}>
                    <ZoomOut className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" onClick={onFitView}>
                    <Maximize2 className="h-4 w-4" />
                </Button>
            </div>

            <Separator orientation="vertical" className="h-6" />

            {/* View Options */}
            <div className="flex items-center gap-1">
                <Button
                    variant={showMiniMap ? "secondary" : "ghost"}
                    size="icon"
                    onClick={toggleMiniMap}
                    title="Toggle MiniMap"
                >
                    <Map className="h-4 w-4" />
                </Button>
                <Button
                    variant={highlightCriticalPath ? "secondary" : "ghost"}
                    size="icon"
                    onClick={toggleCriticalPath}
                    title="Toggle Critical Path"
                >
                    <Route className="h-4 w-4" />
                </Button>
            </div>

            <Separator orientation="vertical" className="h-6" />

            {/* Layout Direction */}
            <div className="flex items-center gap-1">
                <Button
                    variant={layoutDirection === "TB" ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => setLayoutDirection("TB")}
                    className="text-xs"
                >
                    Vertical
                </Button>
                <Button
                    variant={layoutDirection === "LR" ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => setLayoutDirection("LR")}
                    className="text-xs"
                >
                    Horizontal
                </Button>
            </div>
        </div>
    );
}
