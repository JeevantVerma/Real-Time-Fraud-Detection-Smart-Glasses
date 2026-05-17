"""FastAPI application entry point."""

# Standard library imports
import os

# Third-party imports
from fastapi import FastAPI

# Local application imports
from routes.face import router as face_router
from routes.voice import router as voice_router
from routes.risk import router as risk_router

# Initialize FastAPI app
app = FastAPI(title="Fraud Detection Backend", version="0.1.0")

# Ensure uploads directory exists on startup
os.makedirs("uploads", exist_ok=True)

# Include modular routers
app.include_router(face_router)
app.include_router(voice_router)
app.include_router(risk_router)


@app.get("/")
def root():
    """Root health check endpoint."""
    return {"message": "Fraud Detection Backend Running"}
