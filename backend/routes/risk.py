"""Unified risk scoring routes."""

# Third-party imports
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Local application imports
from utils.scoring import fuse_scores, classify_risk

# Create a router for risk-related endpoints
router = APIRouter()


class RiskScoreRequest(BaseModel):
    """Request model for risk score fusion."""

    face_score: float
    voice_score: float


@router.post("/risk-score")
def risk_score(payload: RiskScoreRequest):
    """Return a fused fraud risk score based on face and voice inputs."""
    try:
        score = fuse_scores(payload.face_score, payload.voice_score)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    risk_level, recommendation = classify_risk(score)

    return {
        "risk_level": risk_level,
        "risk_score": score,
        "recommendation": recommendation,
    }
