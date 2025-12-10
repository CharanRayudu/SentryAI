package main

import (
	"log"
	"os"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
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

	// Routes
	api := app.Group("/api/v1")

	api.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{
			"status": "ok",
			"service": "api-go",
		})
	})

	// Mission Control Websocket (Placeholder for now, standard HTTP for MVP)
	// Real implementation would use github.com/gofiber/contrib/websocket
	api.Post("/missions/start", handleStartMission)
	api.Get("/missions/:id", handleGetMission)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}

	log.Printf("Server starting on port %s", port)
	log.Fatal(app.Listen(":" + port))
}

func handleStartMission(c *fiber.Ctx) error {
    // TODO: Trigger Temporal Workflow
    return c.JSON(fiber.Map{"status": "started", "mission_id": "mock-123"})
}

func handleGetMission(c *fiber.Ctx) error {
    return c.JSON(fiber.Map{"id": c.Params("id"), "status": "running"})
}
