package cognitive

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	openai "github.com/sashabaranov/go-openai"
	"sentry/packages/shared"
)

type CognitiveEngine struct {
	client *openai.Client
	Model  string
}

func NewEngine(apiKey string, baseURL string, model string) *CognitiveEngine {
	config := openai.DefaultConfig(apiKey)
	if baseURL != "" {
		config.BaseURL = baseURL
	}
	return &CognitiveEngine{
		client: openai.NewClientWithConfig(config),
		Model:  model,
	}
}

func (e *CognitiveEngine) Think(ctx context.Context, goal string, history []shared.LogEntry, tools []shared.ToolDefinition) (*shared.AgentOutput, error) {
	prompt := e.buildPrompt(goal, history, tools)

	resp, err := e.client.CreateChatCompletion(
		ctx,
		openai.ChatCompletionRequest{
			Model: e.Model,
			Messages: []openai.ChatCompletionMessage{
				{
					Role:    openai.ChatMessageRoleSystem,
					Content: prompt,
				},
				{
					Role:    openai.ChatMessageRoleUser,
					Content: "Analyze the current state and decide the next step.",
				},
			},
			Temperature: 0.2,
		},
	)

	if err != nil {
		return nil, fmt.Errorf("LLM error: %w", err)
	}

	content := resp.Choices[0].Message.Content
	// Clean markdown if present
	content = strings.TrimSpace(content)
	content = strings.TrimPrefix(content, "```json")
	content = strings.TrimPrefix(content, "```")
	content = strings.TrimSuffix(content, "```")

	var output shared.AgentOutput
	if err := json.Unmarshal([]byte(content), &output); err != nil {
		return nil, fmt.Errorf("failed to parse AI response: %w. Raw: %s", err, content)
	}

	return &output, nil
}

func (e *CognitiveEngine) buildPrompt(goal string, history []shared.LogEntry, tools []shared.ToolDefinition) string {
	var sb strings.Builder

	sb.WriteString(`<system_role>
You are SENTRY, an Autonomous Senior Security Engineer.
Your goal is to audit infrastructure, identify vulnerabilities, and verify them safely.
You operate in a Loop: THOUGHT -> PLAN -> ACTION -> OBSERVATION.
</system_role>

<prime_directives>
1. SAFETY FIRST: Never execute destructive commands.
2. SCOPE ADHERENCE: Only scan explicitly allowed targets.
3. NO HALLUCINATION: You cannot "pretend" to run a tool.
4. EVIDENCE BASED: Do not report a vulnerability unless validated.
5. EFFICIENCY: Use minimum steps necessary.
</prime_directives>

<output_format>
You must respond STRICTLY in JSON format.
Schema:
{
  "thought_process": "Analyze previous observation",
  "reasoning": "Why choosing this step",
  "tool_call": { "name": "tool_name", "arguments": {...} } (or null if complete),
  "status_update": "Human readable status",
  "is_complete": false,
  "findings": []
}
</output_format>

<available_tools>
`)

	for _, t := range tools {
		sb.WriteString(fmt.Sprintf("- %s: %s\n", t.Name, t.Description))
	}
	sb.WriteString("</available_tools>\n\n")

	sb.WriteString("<memory_context>\n")
	for i, h := range history {
		sb.WriteString(fmt.Sprintf("Step %d [%s]: %s\n", i+1, h.Type, h.Content))
	}
	sb.WriteString("</memory_context>\n\n")

	sb.WriteString(fmt.Sprintf("<current_goal>\n%s\n</current_goal>", goal))

	return sb.String()
}
