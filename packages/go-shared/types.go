package shared

import (
	"time"
)

// AgentOutput represents the structured output from the AI agent.
// It matches the ReAct schema defined in ai_engine.py.
type AgentOutput struct {
	ThoughtProcess string    `json:"thought_process"`
	Reasoning      string    `json:"reasoning"`
	ToolCall       *ToolCall `json:"tool_call,omitempty"`
	StatusUpdate   string    `json:"status_update"`
	IsComplete     bool      `json:"is_complete"`
	Findings       []Finding `json:"findings"`
}

type ToolCall struct {
	Name      string                 `json:"name"`
	Arguments map[string]interface{} `json:"arguments"`
}

type Finding struct {
	Type     string `json:"type"`     // sqli, xss, etc
	Severity string `json:"severity"` // critical, high, medium, low, info
	Title    string `json:"title"`
	Evidence string `json:"evidence"`
	Location string `json:"location"`
}

// Mission represents a security audit mission.
type Mission struct {
	ID        string    `json:"id"`
	Goal      string    `json:"goal"`
	Status    string    `json:"status"` // pending, running, paused, completed, failed
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// LogEntry for live log streaming
type LogEntry struct {
	Timestamp time.Time `json:"timestamp"`
	MissionID string    `json:"mission_id"`
	Type      string    `json:"type"` // thought, tool_output, error, status
	Content   string    `json:"content"`
}

type ToolDefinition struct {
	Name        string `json:"name"`
	Description string `json:"description"`
}

type AgentPlan struct {
	ThoughtProcess string     `json:"thought_process"`
	Steps          []PlanStep `json:"steps"`
}

type PlanStep struct {
	ID          int    `json:"id"`
	Tool        string `json:"tool"`
	Args        string `json:"args"`
	Description string `json:"description"`
}
