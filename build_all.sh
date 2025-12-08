#!/bin/bash

echo "[SentryAI] Building Service Images..."

cd deploy || exit

# Build images
if command -v docker-compose &> /dev/null; then
    docker-compose build
else
    docker compose build
fi

if [ $? -eq 0 ]; then
    echo "[SentryAI] Build Complete."
else
    echo "[ERROR] Build failed."
    exit 1
fi
