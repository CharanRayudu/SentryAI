@echo off
echo [SentryAI] Stopping System...

cd deploy
docker-compose --env-file ../.env down

echo [SentryAI] Services stopped.
cd ..
pause
