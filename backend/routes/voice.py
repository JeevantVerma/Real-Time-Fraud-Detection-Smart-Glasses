"""Voice verification routes."""

# Standard library imports
import os
import pathlib
import shutil
from uuid import uuid4

# Disable symlinks for Hugging Face downloads on Windows
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")

# SpeechBrain uses pathlib.Path.symlink_to during model fetch
_original_symlink_to = pathlib.Path.symlink_to


def _safe_symlink_to(self, target, target_is_directory=False):
    try:
        _original_symlink_to(self, target, target_is_directory=target_is_directory)
    except OSError:
        shutil.copy2(target, self)


pathlib.Path.symlink_to = _safe_symlink_to

# Third-party imports
from fastapi import APIRouter, File, UploadFile, HTTPException
import torch
import torch.nn.functional as torch_nn
import torchaudio
import soundfile as sf

# SpeechBrain expects torchaudio.set_audio_backend on some versions
if not hasattr(torchaudio, "set_audio_backend"):
    def _noop_backend(_backend):
        return None

    torchaudio.set_audio_backend = _noop_backend

from speechbrain.pretrained import EncoderClassifier

# Reference audio path (place your reference audio here)
REFERENCE_AUDIO_PATH = os.path.join("reference_audio", "reference.wav")


# Load the pretrained speaker recognition model once at startup
SPEAKER_MODEL = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    run_opts={"device": "cpu"},
)

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

    # Ensure reference audio exists
    if not os.path.isfile(REFERENCE_AUDIO_PATH):
        raise HTTPException(
            status_code=500,
            detail="Reference audio not found at reference_audio/reference.wav",
        )

    # Run SpeechBrain verification and clean up the temp file afterwards
    try:
        # Load and normalize uploaded audio (soundfile avoids torchcodec)
        audio_data, sample_rate = sf.read(file_path, dtype="float32")
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)
        waveform = torch.from_numpy(audio_data).unsqueeze(0)

        # Load and normalize reference audio
        ref_data, ref_sample_rate = sf.read(REFERENCE_AUDIO_PATH, dtype="float32")
        if ref_data.ndim > 1:
            ref_data = ref_data.mean(axis=1)
        ref_waveform = torch.from_numpy(ref_data).unsqueeze(0)

        # Resample if needed for both signals
        target_rate = 16000
        if sample_rate != target_rate:
            waveform = torchaudio.functional.resample(
                waveform, orig_freq=sample_rate, new_freq=target_rate
            )
        if ref_sample_rate != target_rate:
            ref_waveform = torchaudio.functional.resample(
                ref_waveform, orig_freq=ref_sample_rate, new_freq=target_rate
            )

        # Extract speaker embeddings
        with torch.no_grad():
            emb_live = SPEAKER_MODEL.encode_batch(waveform).squeeze()
            emb_ref = SPEAKER_MODEL.encode_batch(ref_waveform).squeeze()

        # Cosine similarity between embeddings
        similarity_raw = torch_nn.cosine_similarity(emb_live, emb_ref, dim=0)
        similarity = float(similarity_raw.item())

        # Normalize similarity to 0..1 for cleaner API output
        similarity = max(0.0, min(1.0, (similarity + 1) / 2))
    except RuntimeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid or unsupported audio file",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Voice verification failed",
        ) from exc
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass

    # Determine spoof suspicion based on similarity threshold
    spoof_detected = similarity < 0.75

    # Return the real verification response
    return {
        "module": "voice_verification",
        "voice_similarity": round(similarity, 2),
        "spoof_detected": spoof_detected,
        "status": "success",
    }
