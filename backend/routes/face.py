"""Face verification routes."""

# Standard library imports
import os
from uuid import uuid4

# Third-party imports
from fastapi import APIRouter, File, UploadFile, HTTPException
from deepface import DeepFace

# Reference image path (place your reference image here)
REFERENCE_IMAGE_PATH = os.path.join("reference_faces", "reference.jpg")

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

    # Ensure reference image exists
    if not os.path.isfile(REFERENCE_IMAGE_PATH):
        raise HTTPException(
            status_code=500,
            detail="Reference image not found at reference_faces/reference.jpg",
        )

    # Run DeepFace verification and clean up the temp file afterwards
    try:
        result = DeepFace.verify(
            img1_path=file_path,
            img2_path=REFERENCE_IMAGE_PATH,
            detector_backend="opencv",
            model_name="Facenet",
            enforce_detection=True,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="No face detected or invalid image",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Face verification failed",
        ) from exc
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass

    # Return the real verification response
    return {
        "module": "face_verification",
        "verified": result.get("verified"),
        "distance": result.get("distance"),
        "model": result.get("model"),
        "status": "success",
    }
