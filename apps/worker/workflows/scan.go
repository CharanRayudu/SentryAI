package workflows

import (
	"encoding/json"
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

	// Initial tool definitions
	tools := []shared.ToolDefinition{
		{"subfinder", "Passive subdomain enumeration"},
		{"nuclei", "Vulnerability scanning with templates"},
		{"naabu", "Fast port scanner"},
	}

	// -------------------------------------------------------------------------
	// PHASE 1: PLANNING
	// -------------------------------------------------------------------------
	addLog("[Agent] Analyzing objective and generating execution plan...")
	var plan shared.AgentPlan
	err = workflow.ExecuteActivity(ctx, "GeneratePlan", goal, tools).Get(ctx, &plan)
	if err != nil {
		addLog(fmt.Sprintf("[Error] Plan generation failed: %v", err))
		return "", err
	}

	// Log plan as JSON for API to parse
	planJSON, _ := json.Marshal(plan)
	addLog(fmt.Sprintf("[Plan Proposal] %s", string(planJSON)))
	addLog("[Mission Control] Waiting for plan approval...")

	// Wait for Approval Signal
	var approvalData map[string]interface{}
	signalChan := workflow.GetSignalChannel(ctx, "approve_plan")

	// Wait INDEFINITELY for signal (or until timeout)
	signalChan.Receive(ctx, &approvalData)

	addLog("[Mission Control] Plan approved. Starting execution phase.")

	// -------------------------------------------------------------------------
	// PHASE 2: EXECUTION
	// -------------------------------------------------------------------------

	// Execute steps from the plan
	for _, step := range plan.Steps {
		// Logic to check if step is in approvalData (if we implement granular approval)
		// For now, assume all steps in plan are approved or approvalData contains the modified plan.

		addLog(fmt.Sprintf("[Agent] Executing Step %d: %s (%s)", step.ID, step.Tool, step.Description))

		scanParams := map[string]string{
			"tool":   step.Tool,
			"target": goal, // Simplified: usually target is extracted from args or goal
			"args":   step.Args,
		}

		var toolResult string
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

	// -------------------------------------------------------------------------
	// PHASE 3: REVIEW (Optional ReAct Loop for follow-up)
	// -------------------------------------------------------------------------
	// For MVP, we just finish after plan execution.

	addLog("[Mission Control] All planned steps completed.")
	return "Completed", nil
}
