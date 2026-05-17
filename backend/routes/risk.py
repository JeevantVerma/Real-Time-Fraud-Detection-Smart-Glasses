"""Unified risk scoring routes."""

# Third-party imports
from fastapi import APIRouter

# Local application imports
from utils.scoring import generate_risk_score, classify_risk

# Create a router for risk-related endpoints
router = APIRouter()


@router.get("/risk-score")
def risk_score():
    """Return a simulated unified fraud risk score."""
    # Generate a random risk score
    score = generate_risk_score()

    # Classify the risk level and recommendation
    risk_level, recommendation = classify_risk(score)

    # Return the simulated response
    return {
        "risk_level": risk_level,
        "risk_score": score,
        "recommendation": recommendation,
    }
