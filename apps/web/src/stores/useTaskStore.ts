import { create } from 'zustand';
import { AgentPlan } from '@/types/agent';
import { api } from '@/lib/api';

export interface Task {
    id: string;
    parentId?: string;
    title: string;
    status: 'idle' | 'planning' | 'running' | 'success' | 'failed';
    plan?: AgentPlan;
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

    // Async Actions
    startMission: (prompt: string) => Promise<void>;
}

type MissionStatus = {
    status: string;
};

export const useTaskStore = create<TaskStore>((set, get) => ({
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

    reset: () => set({ tasks: [], activeTaskId: null, omnibarPosition: 'center' }),

    startMission: async (prompt: string) => {
        try {
            // 1. Create potential task locally
            const tempId = Date.now().toString();
            const newTask: Task = {
                id: tempId,
                title: `Mission: ${prompt}`,
                status: 'running',
                logs: ['Requesting mission start...'],
                startTime: Date.now()
            };

            set((state) => ({
                tasks: [...state.tasks, newTask],
                activeTaskId: tempId,
                omnibarPosition: 'top'
            }));

            // 2. Call Backend
            const data = await api.startMission(prompt);

            // 3. Update with real ID
            set((state) => ({
                tasks: state.tasks.map(t => t.id === tempId ? {
                    ...t,
                    id: data.mission_id,
                    logs: [...t.logs, `Mission started. ID: ${data.mission_id}`]
                } : t),
                activeTaskId: data.mission_id
            }));

            // 4. Start Polling (Simple implementation)
            const pollInterval = setInterval(async () => {
                try {
                    const status = await api.getMissionStatus(data.mission_id) as MissionStatus;
                    const normalizedStatus = status.status as Task['status'];

                    const currentTask = get().tasks.find(t => t.id === data.mission_id);
                    // Prevent overwriting 'planning' state with 'running' from polling
                    if (!(currentTask?.status === 'planning' && normalizedStatus === 'running')) {
                        get().updateTask(data.mission_id, { status: normalizedStatus });
                    }

                    if (normalizedStatus === 'success' || normalizedStatus === 'failed') {
                        clearInterval(pollInterval);
                    }
                } catch (e) {
                    console.error("Polling failed", e);
                }
            }, 2000);

        } catch (error) {
            console.error(error);
            // Handle error state
        }
    }
}));
