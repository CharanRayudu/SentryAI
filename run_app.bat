@echo off
echo [SentryAI] Starting System...

if not exist ".env" (
    echo [INFO] .env not found. Creating from default...
    copy .env.example .env
)

cd deploy
docker-compose up -d

echo [SentryAI] Services are starting...
echo   - Dashboard: http://localhost:3000
echo   - API: http://localhost:8000
echo   - Temporal: http://localhost:8233
echo   - Neo4j: http://localhost:7474

cd ..
pause
