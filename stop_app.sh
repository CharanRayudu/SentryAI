#!/bin/bash

echo "[SentryAI] Stopping System..."

# Navigate to deploy directory
cd deploy || exit

# Run Docker Compose with env file from parent directory
if command -v docker-compose &> /dev/null; then
    docker-compose --env-file ../.env down
else
    docker compose --env-file ../.env down
fi

echo "[SentryAI] Services stopped."
