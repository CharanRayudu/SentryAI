from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import chat, schedules, integrations, graph, missions, knowledge
from app.core.events import manager
import asyncio
import os

app = FastAPI(
    title="SentryAI API",
    version="2.0",
    description="Autonomous Security Agent Platform API",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(chat.router, prefix="/api/v1", tags=["Mission Control"])
app.include_router(missions.router, prefix="/api/v1", tags=["Missions"])
app.include_router(schedules.router, prefix="/api/v1", tags=["Schedules"])
app.include_router(graph.router, prefix="/api/v1", tags=["Graph"])
app.include_router(knowledge.router, prefix="/api/v1", tags=["Knowledge"])
app.include_router(integrations.router, prefix="/api/v1", tags=["Integrations"])

@app.on_event("startup")
async def startup_event():
    # Start Redis Listener in background
    asyncio.create_task(manager.subscribe_to_channels())

@app.get("/health")
async def health_check():
    return {"status": "operational", "mode": "socket-enabled"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
