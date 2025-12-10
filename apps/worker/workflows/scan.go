package workflows

import (
	"time"

	"go.temporal.io/sdk/workflow"
	"sentry/packages/shared"
)

func SecurityScanWorkflow(ctx workflow.Context, missionID string, goal string) (string, error) {
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 10 * time.Minute,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Security Scan Workflow", "MissionID", missionID)

	var history []shared.LogEntry
	// Initial tool definitions (static for now, can be dynamic)
	tools := []shared.ToolDefinition{
		{"subfinder", "Passive subdomain enumeration"},
		{"nuclei", "Vulnerability scanning with templates"},
		{"naabu", "Fast port scanner"},
	}

	maxSteps := 50
	for i := 0; i < maxSteps; i++ {
		// 1. Think
		var agentOutput shared.AgentOutput
		err := workflow.ExecuteActivity(ctx, "AIThink", goal, history, tools).Get(ctx, &agentOutput)
		if err != nil {
			return "", err
		}

		// Log thought
		history = append(history, shared.LogEntry{
			Timestamp: time.Now(),
			MissionID: missionID,
			Type:      "thought",
			Content:   agentOutput.ThoughtProcess,
		})

		// Check completion
		if agentOutput.IsComplete {
			return "Completed", nil
		}

		// 2. Act
		if agentOutput.ToolCall != nil {
			var toolResult string
			params := agentOutput.ToolCall.Arguments
			// Flatten args map to string for legacy docker wrapper compatibility if needed
			// But our Activity expects struct. We need to map it.
			// Ideally we use a specific struct.
            
            // Re-marshal to JSON to handle generic map to string? 
            // Simplified: Assume args has "args" and "target" keys as string
            
            target, _ := params["target"].(string)
            args, _ := params["args"].(string)
            // fallback logic or cleaner struct needed. 

			scanParams := map[string]string{
                "tool": agentOutput.ToolCall.Name,
                "target": target,
                "args": args,
            }

			err = workflow.ExecuteActivity(ctx, "RunToolScan", scanParams).Get(ctx, &toolResult)
			if err != nil {
				toolResult = "Error executing tool: " + err.Error()
			}

			history = append(history, shared.LogEntry{
				Timestamp: time.Now(),
				MissionID: missionID,
				Type:      "tool_output",
				Content:   toolResult,
			})
		}
	}

	return "Max steps reached", nil
}
