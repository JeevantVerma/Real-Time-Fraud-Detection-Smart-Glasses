"""Voice verification routes."""

# Standard library imports
import os
from uuid import uuid4

# Third-party imports
from fastapi import APIRouter, File, UploadFile, HTTPException

# Local application imports
from utils.scoring import generate_voice_score

# Create a router for voice-related endpoints
router = APIRouter()


@router.post("/voice-check")
async def voice_check(audio: UploadFile = File(...)):
    """Handle voice verification requests."""
    # Validate file presence
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")

    # Ensure uploads directory exists
    os.makedirs("uploads", exist_ok=True)

    # Create a unique filename to avoid collisions
    file_ext = os.path.splitext(audio.filename)[1] or ".audio"
    safe_name = f"voice_{uuid4().hex}{file_ext}"
    file_path = os.path.join("uploads", safe_name)

    # Save the uploaded audio to disk
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await audio.read())
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to save audio") from exc

    # Generate a simulated voice score
    score = generate_voice_score()

    # Determine if spoofing is detected based on the score
    spoof_detected = score < 0.75

    # Return the simulated response
    return {
        "module": "voice_verification",
        "voice_real_score": score,
        "spoof_detected": spoof_detected,
        "status": "success",
    }
