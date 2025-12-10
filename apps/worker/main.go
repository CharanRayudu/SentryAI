package main

import (
	"log"
	"os"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"

	"sentry/apps/worker/activities"
	"sentry/apps/worker/cognitive"
	"sentry/apps/worker/workflows"
)

func main() {
	// 1. Initialize Cognitive Engine
	apiKey := os.Getenv("NVIDIA_API_KEY")
	if apiKey == "" {
		log.Println("Warning: NVIDIA_API_KEY not set. AI capabilities will fail.")
	}
    // Using an OpenAI-compatible endpoint (like NVIDIA NIM or actual OpenAI)
    // Defaulting to NVIDIA NIM base URL if not set, or OpenAI default
    baseURL := os.Getenv("AI_BASE_URL") 
    if baseURL == "" {
        baseURL = "https://integrate.api.nvidia.com/v1" // Example NIM URL
    }
    model := os.Getenv("AI_MODEL") 
    if model == "" {
        model = "mistralai/mixtral-8x22b-instruct-v0.1"
    }

	engine := cognitive.NewEngine(apiKey, baseURL, model)

	// 2. Initialize Activities
	acts, err := activities.NewActivities(engine)
	if err != nil {
		log.Fatalln("Unable to metadata docker client", err)
	}

	// 3. Connect to Temporal
	host := os.Getenv("TEMPORAL_HOST")
	if host == "" {
		host = "localhost:7233"
	}

	c, err := client.Dial(client.Options{
		HostPort: host,
	})
	if err != nil {
		log.Fatalln("Unable to create client", err)
	}
	defer c.Close()

	// 4. Register Worker
	w := worker.New(c, "sentry-tasks", worker.Options{})

	w.RegisterWorkflow(workflows.SecurityScanWorkflow)
	w.RegisterActivity(acts.AIThink)
	w.RegisterActivity(acts.RunToolScan)

	log.Println("Worker started...")
	err = w.Run(worker.InterruptCh())
	if err != nil {
		log.Fatalln("Unable to start worker", err)
	}
}
