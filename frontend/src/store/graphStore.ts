import { create } from "zustand";

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

export const useGraphStore = create<GraphState>((set) => ({
    selectedNodeId: null,
    highlightCriticalPath: true,
    showMiniMap: true,
    layoutDirection: "TB",

    setSelectedNodeId: (id) => set({ selectedNodeId: id }),
    toggleCriticalPath: () =>
        set((state) => ({ highlightCriticalPath: !state.highlightCriticalPath })),
    toggleMiniMap: () => set((state) => ({ showMiniMap: !state.showMiniMap })),
    setLayoutDirection: (direction) => set({ layoutDirection: direction }),
}));
