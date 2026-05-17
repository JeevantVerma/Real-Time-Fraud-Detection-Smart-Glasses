"""Face verification routes."""

# Standard library imports
import os
from uuid import uuid4

# Third-party imports
from fastapi import APIRouter, File, UploadFile, HTTPException

# Local application imports
from utils.scoring import generate_face_score

# Create a router for face-related endpoints
router = APIRouter()


@router.post("/face-check")
async def face_check(image: UploadFile = File(...)):
    """Handle face verification requests."""
    # Validate file presence
    if not image.filename:
        raise HTTPException(status_code=400, detail="No image file provided")

    # Ensure uploads directory exists
    os.makedirs("uploads", exist_ok=True)

    # Create a unique filename to avoid collisions
    file_ext = os.path.splitext(image.filename)[1] or ".img"
    safe_name = f"face_{uuid4().hex}{file_ext}"
    file_path = os.path.join("uploads", safe_name)

    # Save the uploaded image to disk
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to save image") from exc

    # Generate a simulated face match score
    score = generate_face_score()

    # Determine if the person is the same based on the score
    same_person = score > 0.80

    # Return the simulated response
    return {
        "module": "face_verification",
        "face_match_score": score,
        "same_person": same_person,
        "status": "success",
    }
