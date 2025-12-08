#!/bin/bash

echo "[SentryAI] Starting System..."

# Ensure .env exists
if [ ! -f .env ]; then
    echo "[INFO] .env not found. Creating from default..."
    cp .env.example .env
fi

# Navigate to deploy directory
cd deploy || exit

# Run Docker Compose
# Use 'docker compose' if v2, fallback to 'docker-compose'
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

echo "[SentryAI] Services are starting..."
echo "  - Dashboard: http://localhost:3000"
echo "  - API:       http://localhost:8000"
echo "  - Temporal:  http://localhost:8233"
echo "  - Neo4j:     http://localhost:7474"
