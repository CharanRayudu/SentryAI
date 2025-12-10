package main

import (
	"context"
	"log"
	"os"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"github.com/gofiber/websocket/v2"
	"go.temporal.io/sdk/client"
	"strings"
	"sync"
)

func main() {
	// Initialize Fiber
	app := fiber.New(fiber.Config{
		AppName: "SentryAI API",
	})

	// Middleware
	app.Use(logger.New())
	app.Use(recover.New())
	app.Use(cors.New(cors.Config{
		AllowOrigins: "*",
		AllowHeaders: "Origin, Content-Type, Accept",
	}))

	// 3. Connect to Temporal
	host := os.Getenv("TEMPORAL_HOST")
	if host == "" {
		host = "localhost:7233"
	}

	c, err := client.Dial(client.Options{
		HostPort: host,
	})
	if err != nil {
		log.Fatalln("Unable to create Temporal client", err)
	}
	defer c.Close()

	// WebSocket upgrade gate
	app.Use("/api/v1/ws/mission", func(ctx *fiber.Ctx) error {
		if websocket.IsWebSocketUpgrade(ctx) {
			return ctx.Next()
		}
		return fiber.ErrUpgradeRequired
	})

	// Routes
	api := app.Group("/api/v1")

	api.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{
			"status":  "ok",
			"service": "api-go",
		})
	})

	api.Post("/missions/start", func(ctx *fiber.Ctx) error {
		return handleStartMission(ctx, c)
	})
	api.Get("/missions/:id", func(ctx *fiber.Ctx) error {
		return handleGetMission(ctx, c)
	})
	api.Post("/missions/:id/stop", func(ctx *fiber.Ctx) error {
		return handleStopMission(ctx, c)
	})
	api.Get("/ws/mission", missionWebSocketHandler(c))

	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}

	log.Printf("Server starting on port %s", port)
	log.Fatal(app.Listen(":" + port))
}

type MissionRequest struct {
	Prompt string `json:"prompt"`
}

func handleStartMission(c *fiber.Ctx, tc client.Client) error {
	var req MissionRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request body"})
	}

	missionID, runID, err := startMissionWorkflow(tc, req.Prompt)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Failed to start mission", "details": err.Error()})
	}

	return c.JSON(fiber.Map{
		"status":     "started",
		"mission_id": missionID,
		"run_id":     runID,
	})
}

func handleGetMission(c *fiber.Ctx, tc client.Client) error {
	missionID := c.Params("id")

	logs, err := fetchMissionLogs(context.Background(), tc, missionID)
	if err != nil {
		return c.JSON(fiber.Map{"id": missionID, "status": "unknown", "logs": []string{}})
	}

	status := deriveStatus(logs)

	return c.JSON(fiber.Map{
		"id":     missionID,
		"status": status,
		"logs":   logs,
	})
}

type stopMissionRequest struct {
	RunID string `json:"run_id"`
}

func handleStopMission(c *fiber.Ctx, tc client.Client) error {
	missionID := c.Params("id")
	var req stopMissionRequest
	_ = c.BodyParser(&req)

	if missionID == "" {
		return c.Status(400).JSON(fiber.Map{"error": "mission_id required"})
	}

	if err := stopMissionWorkflow(tc, missionID, req.RunID); err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Failed to stop mission", "details": err.Error()})
	}

	return c.JSON(fiber.Map{
		"status":     "stopped",
		"mission_id": missionID,
	})
}

// missionWebSocketHandler provides a lightweight mission channel matching the frontend hook.
func missionWebSocketHandler(tc client.Client) fiber.Handler {
	return websocket.New(func(conn *websocket.Conn) {
		defer conn.Close()

		ctx, cancel := context.WithCancel(context.Background())
		defer cancel()

		out := make(chan map[string]interface{}, 32)
		var writerWG sync.WaitGroup
		writerWG.Add(1)
		go func() {
			defer writerWG.Done()
			for msg := range out {
				if err := conn.WriteJSON(msg); err != nil {
					cancel()
					return
				}
			}
		}()

		// Track the active mission stream so we can stop it on disconnect or when starting a new mission.
		var streamWG sync.WaitGroup
		var currentCancel context.CancelFunc
		var currentMissionID string
		var currentRunID string

		send := func(msg map[string]interface{}) {
			select {
			case out <- msg:
			case <-ctx.Done():
			}
		}

		send(map[string]interface{}{
			"type":    "server:connected",
			"message": "mission channel ready",
		})

		for {
			var incoming map[string]interface{}
			if err := conn.ReadJSON(&incoming); err != nil {
				cancel()
				break
			}

			switch incoming["type"] {
			case "client:ping":
				send(map[string]interface{}{"type": "server:pong"})
			case "client:message":
				prompt, _ := incoming["content"].(string)
				if prompt == "" {
					send(map[string]interface{}{"type": "server:error", "message": "missing mission content"})
					continue
				}

				// Stop any previous stream before starting a new mission
				if currentCancel != nil {
					currentCancel()
					streamWG.Wait()
				}

				missionCtx, missionCancel := context.WithCancel(ctx)
				currentCancel = missionCancel
				currentMissionID = ""
				currentRunID = ""

				send(map[string]interface{}{
					"type":   "server:agent_thought",
					"status": "processing",
					"log":    "Analyzing mission objective...",
				})

				missionID, runID, err := startMissionWorkflow(tc, prompt)
				if err != nil {
					send(map[string]interface{}{"type": "server:error", "message": err.Error()})
					continue
				}

				send(map[string]interface{}{
					"type":       "server:job_status",
					"mission_id": missionID,
					"run_id":     runID,
					"status":     "started",
				})

				currentMissionID = missionID
				currentRunID = runID

				// Provide a simple plan preview for the Command Center UI.
				send(map[string]interface{}{
					"type":    "server:plan_proposal",
					"plan_id": missionID,
					"intent":  prompt,
					"steps": []map[string]interface{}{
						{"id": 1, "tool": "subfinder", "args": "-d <target>", "enabled": true},
						{"id": 2, "tool": "naabu", "args": "-host <target>", "enabled": true},
						{"id": 3, "tool": "nuclei", "args": "-u <target>", "enabled": true},
					},
				})

				streamWG.Add(1)
				go func() {
					defer streamWG.Done()
					streamMissionLogs(missionCtx, tc, missionID, out)
				}()
			case "client:stop":
				missionID, _ := incoming["mission_id"].(string)
				runID, _ := incoming["run_id"].(string)
				if missionID == "" {
					missionID = currentMissionID
				}
				if runID == "" {
					runID = currentRunID
				}

				if missionID == "" {
					send(map[string]interface{}{"type": "server:error", "message": "no active mission to stop"})
					continue
				}

				if err := stopMissionWorkflow(tc, missionID, runID); err != nil {
					send(map[string]interface{}{"type": "server:error", "message": err.Error()})
					continue
				}

				if currentCancel != nil {
					currentCancel()
					streamWG.Wait()
				}

				send(map[string]interface{}{
					"type":       "server:job_status",
					"mission_id": missionID,
					"status":     "stopped",
				})
			default:
				send(map[string]interface{}{"type": "server:error", "message": "unknown message type"})
			}
		}

		// Cleanup
		if currentCancel != nil {
			currentCancel()
		}
		streamWG.Wait()
		close(out)
		writerWG.Wait()
	})
}

func startMissionWorkflow(tc client.Client, prompt string) (string, string, error) {
	missionID := "mission-" + time.Now().Format("20060102-150405")
	options := client.StartWorkflowOptions{
		ID:        missionID,
		TaskQueue: "sentry-tasks",
	}

	we, err := tc.ExecuteWorkflow(context.Background(), options, "SecurityScanWorkflow", missionID, prompt)
	if err != nil {
		return "", "", err
	}

	return we.GetID(), we.GetRunID(), nil
}

func stopMissionWorkflow(tc client.Client, missionID string, runID string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return tc.CancelWorkflow(ctx, missionID, runID)
}

func fetchMissionLogs(ctx context.Context, tc client.Client, missionID string) ([]string, error) {
	val, err := tc.QueryWorkflow(ctx, missionID, "", "get_logs")
	if err != nil {
		return nil, err
	}

	var logs []string
	if err := val.Get(&logs); err != nil {
		return nil, err
	}

	return logs, nil
}

func deriveStatus(logs []string) string {
	if len(logs) == 0 {
		return "running"
	}

	lastLog := logs[len(logs)-1]
	switch {
	case strings.Contains(lastLog, "successfully completed"):
		return "success"
	case strings.Contains(strings.ToLower(lastLog), "cancel"):
		return "stopped"
	case strings.Contains(lastLog, "Max steps reached"):
		return "failed"
	default:
		return "running"
	}
}

func streamMissionLogs(ctx context.Context, tc client.Client, missionID string, out chan<- map[string]interface{}) {
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	lastCount := 0

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			logs, err := fetchMissionLogs(ctx, tc, missionID)
			if err != nil {
				select {
				case out <- map[string]interface{}{"type": "server:error", "message": err.Error()}:
				case <-ctx.Done():
				}
				return
			}

			if len(logs) > lastCount {
				newLogs := logs[lastCount:]
				for _, line := range newLogs {
					eventType := "server:job_log"
					if strings.Contains(line, "[Agent]") {
						eventType = "server:agent_thought"
					}
					select {
					case out <- map[string]interface{}{
						"type":       eventType,
						"mission_id": missionID,
						"log":        line,
					}:
					case <-ctx.Done():
						return
					}
				}
				lastCount = len(logs)
			}

			status := deriveStatus(logs)
			select {
			case out <- map[string]interface{}{"type": "server:job_status", "mission_id": missionID, "status": status}:
			case <-ctx.Done():
				return
			}

			if status == "success" || status == "failed" {
				return
			}
		}
	}
}
