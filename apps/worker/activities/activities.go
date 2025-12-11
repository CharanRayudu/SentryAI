package activities

import (
	"context"
	"fmt"
	"io"
	"strings"

	"sentry/apps/worker/cognitive"
	"sentry/packages/shared"

	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/client"
	"go.temporal.io/sdk/activity"
)

type Activities struct {
	Docker *client.Client
	Engine *cognitive.CognitiveEngine
}

func NewActivities(engine *cognitive.CognitiveEngine) (*Activities, error) {
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		return nil, err
	}
	return &Activities{Docker: cli, Engine: engine}, nil
}

type ScanParams struct {
	Tool   string `json:"tool"`
	Target string `json:"target"`
	Args   string `json:"args"`
}

func (a *Activities) RunToolScan(ctx context.Context, params ScanParams) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Starting tool scan", "tool", params.Tool, "target", params.Target)

	imageMap := map[string]string{
		"subfinder": "projectdiscovery/subfinder:latest",
		"nuclei":    "projectdiscovery/nuclei:latest",
		"naabu":     "projectdiscovery/naabu:latest",
	}

	image, ok := imageMap[params.Tool]
	if !ok {
		return "", fmt.Errorf("unknown tool: %s", params.Tool)
	}

	// Construct command
	cmdStr := params.Args
	if params.Tool == "subfinder" && !strings.Contains(params.Args, "-d") {
		cmdStr = fmt.Sprintf("-d %s %s", params.Target, params.Args)
	} else if params.Tool == "nuclei" && !strings.Contains(params.Args, "-u") {
		cmdStr = fmt.Sprintf("-u %s %s", params.Target, params.Args)
	} else if params.Tool == "naabu" && !strings.Contains(params.Args, "-host") {
		cmdStr = fmt.Sprintf("-host %s %s", params.Target, params.Args)
	}

	// Use shell parsing or simple split? Docker needs []string
	cmd := strings.Fields(cmdStr)

	resp, err := a.Docker.ContainerCreate(ctx, &container.Config{
		Image: image,
		Cmd:   cmd,
		Tty:   false,
	}, nil, nil, nil, "")
	if err != nil {
		return "", fmt.Errorf("failed to create container: %w", err)
	}

	if err := a.Docker.ContainerStart(ctx, resp.ID, container.StartOptions{}); err != nil {
		return "", fmt.Errorf("failed to start container: %w", err)
	}

	statusCh, errCh := a.Docker.ContainerWait(ctx, resp.ID, container.WaitConditionNotRunning)
	select {
	case err := <-errCh:
		if err != nil {
			return "", fmt.Errorf("error waiting for container: %w", err)
		}
	case <-statusCh:
	}

	out, err := a.Docker.ContainerLogs(ctx, resp.ID, container.LogsOptions{ShowStdout: true, ShowStderr: true})
	if err != nil {
		return "", fmt.Errorf("failed to get logs: %w", err)
	}

	// Read logs
	output, err := io.ReadAll(out)
	if err != nil {
		return "", err
	}

	// cleanup
	_ = a.Docker.ContainerRemove(ctx, resp.ID, container.RemoveOptions{})

	return string(output), nil
}

func (a *Activities) AIThink(ctx context.Context, goal string, history []shared.LogEntry, tools []shared.ToolDefinition) (*shared.AgentOutput, error) {
	return a.Engine.Think(ctx, goal, history, tools)
}

func (a *Activities) GeneratePlan(ctx context.Context, goal string, tools []shared.ToolDefinition) (*shared.AgentPlan, error) {
	return a.Engine.Plan(ctx, goal, tools)
}
