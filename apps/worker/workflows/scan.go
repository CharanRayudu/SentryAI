package workflows

import (
	"fmt"
	"time"

	"sentry/packages/shared"

	"go.temporal.io/sdk/workflow"
)

func SecurityScanWorkflow(ctx workflow.Context, missionID string, goal string) (string, error) {
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 10 * time.Minute,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Security Scan Workflow", "MissionID", missionID)

	// Workflow State
	var history []shared.LogEntry
	var logs []string

	// Query Handler for Logs
	err := workflow.SetQueryHandler(ctx, "get_logs", func() ([]string, error) {
		return logs, nil
	})
	if err != nil {
		logger.Info("SetQueryHandler failed", "Error", err)
		return "", err
	}

	// Helper to add log
	addLog := func(msg string) {
		logs = append(logs, msg)
	}

	addLog(fmt.Sprintf("[Mission Control] Initializing mission: %s", missionID))
	addLog(fmt.Sprintf("[Mission Control] Goal: %s", goal))

	// Initial tool definitions (static for now, can be dynamic)
	tools := []shared.ToolDefinition{
		{"subfinder", "Passive subdomain enumeration"},
		{"nuclei", "Vulnerability scanning with templates"},
		{"naabu", "Fast port scanner"},
	}

	maxSteps := 50
	for i := 0; i < maxSteps; i++ {
		// 1. Think
		addLog("[Agent] Analyzing situation...")
		var agentOutput shared.AgentOutput
		err := workflow.ExecuteActivity(ctx, "AIThink", goal, history, tools).Get(ctx, &agentOutput)
		if err != nil {
			addLog(fmt.Sprintf("[Error] AI Think failed: %v", err))
			return "", err
		}

		// Log thought
		history = append(history, shared.LogEntry{
			Timestamp: time.Now(),
			MissionID: missionID,
			Type:      "thought",
			Content:   agentOutput.ThoughtProcess,
		})
		addLog(fmt.Sprintf("[Agent] Thought: %s", agentOutput.ThoughtProcess))

		// Check completion
		if agentOutput.IsComplete {
			addLog("[Mission Control] Mission successfully completed.")
			return "Completed", nil
		}

		// 2. Act
		if agentOutput.ToolCall != nil {
			addLog(fmt.Sprintf("[Agent] Executing tool: %s", agentOutput.ToolCall.Name))
			var toolResult string
			params := agentOutput.ToolCall.Arguments

			target, _ := params["target"].(string)
			args, _ := params["args"].(string)

			scanParams := map[string]string{
				"tool":   agentOutput.ToolCall.Name,
				"target": target,
				"args":   args,
			}

			err = workflow.ExecuteActivity(ctx, "RunToolScan", scanParams).Get(ctx, &toolResult)
			if err != nil {
				toolResult = "Error executing tool: " + err.Error()
				addLog(fmt.Sprintf("[Error] Tool execution failed: %v", err))
			} else {
				addLog(fmt.Sprintf("[Tool Output] %s", toolResult))
			}

			history = append(history, shared.LogEntry{
				Timestamp: time.Now(),
				MissionID: missionID,
				Type:      "tool_output",
				Content:   toolResult,
			})
		}
	}

	addLog("[Mission Control] Max steps reached. Aborting.")
	return "Max steps reached", nil
}
