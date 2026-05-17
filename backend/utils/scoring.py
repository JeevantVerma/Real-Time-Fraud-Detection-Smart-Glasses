"""Utility functions for generating simulated scores."""

# Standard library imports
import random


def _round_score(value: float) -> float:
    """Round scores to two decimal places for clean output."""
    return round(value, 2)


def generate_face_score() -> float:
    """Generate a random face match confidence score."""
    return _round_score(random.uniform(0.70, 0.99))


def generate_voice_score() -> float:
    """Generate a random voice authenticity score."""
    return _round_score(random.uniform(0.60, 0.99))


def generate_risk_score() -> float:
    """Generate a random fraud risk score."""
    return _round_score(random.uniform(0.0, 1.0))


def classify_risk(score: float) -> tuple[str, str]:
    """Classify risk level and recommendation based on score."""
    if score < 0.3:
        return "SAFE", "Proceed"
    if score <= 0.7:
        return "SUSPICIOUS", "Review Manually"
    return "FRAUD", "Block and Investigate"
