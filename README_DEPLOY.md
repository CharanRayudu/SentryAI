# SentryAI Deployment Guide

## 🐳 "Run Anywhere"

SentryAI is containerized, meaning you can run it on any machine with Docker installed.

### Pre-requisites
- **Docker Desktop** (or Docker Engine + Compose)
- **Git** (optional, to clone repo)

### 🚀 Quick Start (Windows)
1. Double-click **`run_app.bat`**.
2. Wait for the containers to spin up.

### 🐧 Quick Start (Linux / macOS)
1. Open a terminal.
2. Give execution permissions:
   ```bash
   chmod +x run_app.sh build_all.sh
   ```
3. Run the start script:
   ```bash
   ./run_app.sh
   ```

### 🛠️ Manual Start (Docker CLI)
1. Ensure `.env` exists:
   ```bash
   cp .env.example .env
   ```
2. Run Docker Compose:
   ```bash
   cd deploy
   docker-compose up -d --build
   ```

### 📦 Updating Images
To rebuild specific services after code changes:
- Run **`build_all.bat`**
- OR: `docker-compose build`

### 🔑 Default Credentials
- **Neo4j**: neo4j / sentry_password
- **Postgres**: sentry / sentry_password
