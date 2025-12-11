export interface PlanStep {
    id: number;
    tool: string;
    args: string;
    description: string;
}

export interface AgentPlan {
    thought_process: string;
    steps: PlanStep[];
}
