"""Utility functions for risk fusion."""


def _round_score(value: float) -> float:
    """Round scores to two decimal places for clean output."""
    return round(value, 2)


def _validate_score(value: float, label: str) -> None:
    """Validate that a score is within 0..1."""
    if value < 0 or value > 1:
        raise ValueError(f"{label} must be between 0 and 1")


def fuse_scores(face_score: float, voice_score: float) -> float:
    """Combine face and voice scores with weighted fusion."""
    _validate_score(face_score, "face_score")
    _validate_score(voice_score, "voice_score")
    fused = (face_score * 0.6) + (voice_score * 0.4)
    return _round_score(fused)


def classify_risk(score: float) -> tuple[str, str]:
    """Classify risk level and recommendation based on score."""
    if score >= 0.8:
        return "SAFE", "Proceed"
    if score >= 0.5:
        return "SUSPICIOUS", "Manual verification advised"
    return "FRAUD", "High fraud probability detected"
