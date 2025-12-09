@echo off
echo [SentryAI] Building Service Images...

cd deploy
docker-compose --env-file ../.env build --parallel

if %errorlevel% neq 0 (
    echo [ERROR] Build failed.
    exit /b %errorlevel%
)

echo [SentryAI] Build Complete. Images tagged:
echo   - sentry-web:latest
echo   - sentry-api:latest
echo   - sentry-worker:latest
cd ..
pause
