import { create } from "zustand";
import { persist } from "zustand/middleware";

interface GraphState {
    selectedNodeId: string | null;
    highlightCriticalPath: boolean;
    showMiniMap: boolean;
    layoutDirection: "TB" | "LR";

    setSelectedNodeId: (id: string | null) => void;
    toggleCriticalPath: () => void;
    toggleMiniMap: () => void;
    setLayoutDirection: (direction: "TB" | "LR") => void;
}

export const useGraphStore = create<GraphState>()(
    persist(
        (set) => ({
            selectedNodeId: null,
            highlightCriticalPath: true,
            showMiniMap: true,
            layoutDirection: "LR",  // Default to horizontal (left-to-right) layout

            setSelectedNodeId: (id) => set({ selectedNodeId: id }),
            toggleCriticalPath: () =>
                set((state) => ({ highlightCriticalPath: !state.highlightCriticalPath })),
            toggleMiniMap: () => set((state) => ({ showMiniMap: !state.showMiniMap })),
            setLayoutDirection: (direction) => set({ layoutDirection: direction }),
        }),
        {
            name: "graph-settings",
            partialize: (state) => ({
                // Only persist these preferences (not selectedNodeId)
                highlightCriticalPath: state.highlightCriticalPath,
                showMiniMap: state.showMiniMap,
                layoutDirection: state.layoutDirection,
            }),
        }
    )
);

