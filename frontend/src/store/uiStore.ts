import { create } from "zustand";

interface UIState {
    sidebarOpen: boolean;
    toggleSidebar: () => void;
    setSidebarOpen: (open: boolean) => void;

    // Modals
    uploadModalOpen: boolean;
    setUploadModalOpen: (open: boolean) => void;

    // Filters
    taskStatusFilter: string | null;
    taskPriorityFilter: string | null;
    setTaskStatusFilter: (status: string | null) => void;
    setTaskPriorityFilter: (priority: string | null) => void;
    clearFilters: () => void;
}

export const useUIStore = create<UIState>((set) => ({
    sidebarOpen: true,
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
    setSidebarOpen: (open) => set({ sidebarOpen: open }),

    uploadModalOpen: false,
    setUploadModalOpen: (open) => set({ uploadModalOpen: open }),

    taskStatusFilter: null,
    taskPriorityFilter: null,
    setTaskStatusFilter: (status) => set({ taskStatusFilter: status }),
    setTaskPriorityFilter: (priority) => set({ taskPriorityFilter: priority }),
    clearFilters: () =>
        set({
            taskStatusFilter: null,
            taskPriorityFilter: null,
        }),
}));
