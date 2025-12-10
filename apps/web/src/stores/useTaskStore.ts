import { create } from 'zustand';

export interface Task {
    id: string;
    parentId?: string;
    title: string;
    status: 'idle' | 'running' | 'success' | 'failed';
    logs: string[];
    artifacts?: { type: 'file' | 'diff'; url: string; name: string }[];
    startTime: number;
    endTime?: number;
}

interface TaskStore {
    tasks: Task[];
    activeTaskId: string | null;
    omnibarPosition: 'center' | 'top';

    // Actions
    addTask: (task: Task) => void;
    updateTask: (id: string, updates: Partial<Task>) => void;
    appendLog: (taskId: string, log: string) => void;
    setOmnibarPosition: (pos: 'center' | 'top') => void;
    reset: () => void;
}

export const useTaskStore = create<TaskStore>((set) => ({
    tasks: [],
    activeTaskId: null,
    omnibarPosition: 'center',

    addTask: (task) => set((state) => ({
        tasks: [...state.tasks, task],
        activeTaskId: task.id
    })),

    updateTask: (id, updates) => set((state) => ({
        tasks: state.tasks.map((t) => t.id === id ? { ...t, ...updates } : t)
    })),

    appendLog: (taskId, log) => set((state) => ({
        tasks: state.tasks.map((t) =>
            t.id === taskId ? { ...t, logs: [...t.logs, log] } : t
        )
    })),

    setOmnibarPosition: (pos) => set({ omnibarPosition: pos }),

    reset: () => set({ tasks: [], activeTaskId: null, omnibarPosition: 'center' })
}));
