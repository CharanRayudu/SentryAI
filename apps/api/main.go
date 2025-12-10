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
	"go.temporal.io/sdk/client"
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

	missionID := "mission-" + time.Now().Format("20060102-150405")
	options := client.StartWorkflowOptions{
		ID:        missionID,
		TaskQueue: "sentry-tasks",
	}

	we, err := tc.ExecuteWorkflow(context.Background(), options, "SecurityScanWorkflow", missionID, req.Prompt)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Failed to start mission", "details": err.Error()})
	}

	return c.JSON(fiber.Map{
		"status":     "started",
		"mission_id": we.GetID(),
		"run_id":     we.GetRunID(),
	})
}

func handleGetMission(c *fiber.Ctx, tc client.Client) error {
	missionID := c.Params("id")

	// Query for logs
	val, err := tc.QueryWorkflow(context.Background(), missionID, "", "get_logs")
	if err != nil {
		// If workflow not found or query failed, return simplistic status
		return c.JSON(fiber.Map{"id": missionID, "status": "unknown", "logs": []string{}})
	}

	var logs []string
	if err := val.Get(&logs); err != nil {
		logs = []string{"Error decoding logs"}
	}

	// Helper to determine status from logs or workflow state (simplified)
	status := "running"
	// Check if workflow is closed (omitted for brevity, utilizing logs to guess status for now)
	if len(logs) > 0 {
		lastLog := logs[len(logs)-1]
		if lastLog == "[Mission Control] Mission successfully completed." {
			status = "success"
		} else if lastLog == "[Mission Control] Max steps reached. Aborting." {
			status = "failed"
		}
	}

	return c.JSON(fiber.Map{
		"id":     missionID,
		"status": status,
		"logs":   logs,
	})
}
