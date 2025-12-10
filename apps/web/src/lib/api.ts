export const API_BASE = '/api/v1';

export interface MissionResponse {
    mission_id: string;
    status: string;
}

export interface TaskStatusResponse {
    id: string;
    status: 'idle' | 'running' | 'success' | 'failed';
    logs: string[];
}

export const api = {
    startMission: async (prompt: string): Promise<MissionResponse> => {
        const res = await fetch(`${API_BASE}/missions/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        if (!res.ok) throw new Error('Failed to start mission');
        return res.json();
    },

    getMissionStatus: async (missionId: string): Promise<TaskStatusResponse> => {
        const res = await fetch(`${API_BASE}/missions/${missionId}`);
        if (!res.ok) throw new Error('Failed to fetch mission status');
        return res.json();
    }
};
