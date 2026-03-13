"""
Voice-Enabled Logistics Assistant
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import shipments, tasks, voice, auth

app = FastAPI(
    title="Voice-Enabled Logistics Assistant",
    description=(
        "Hands-free shipment tracking and task management for drivers "
        "and warehouse workers. Speak natural-language commands to query "
        "shipments, update task status, and receive spoken responses."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(shipments.router, prefix="/shipments", tags=["Shipments"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(voice.router, prefix="/voice", tags=["Voice"])


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "Voice-Enabled Logistics Assistant",
        "version": "1.0.0",
    }
