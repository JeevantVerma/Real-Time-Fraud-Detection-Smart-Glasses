# Real-Time Fraud Detection Smart Glasses - Phase A (Backend)

This backend provides face verification, voice verification, and unified risk scoring APIs.

## Project Structure

```
backend/
│
├── app.py
├── routes/
│   ├── face.py
│   ├── voice.py
│   └── risk.py
│
├── utils/
│   └── scoring.py
│
├── reference_faces/
│   └── reference.jpg
│
├── reference_audio/
│   └── reference.wav
│
├── uploads/
│   └── .gitkeep
│
├── requirements.txt
│
└── README.md
```

## Setup Instructions

1. Open a terminal in the `backend` folder.
2. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Server

```bash
uvicorn app:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Testing Instructions

### Root Check

```
GET /
```

Response:

```json
{
  "message": "Fraud Detection Backend Running"
}
```

### Face Verification

```
POST /face-check
```

- Upload a file with the form field name `image`.
- The uploaded image is compared to `reference_faces/reference.jpg` using DeepFace.

Example curl:

```bash
curl -X POST "http://127.0.0.1:8000/face-check" \
  -F "image=@/path/to/image.jpg"
```

### Voice Verification

```
POST /voice-check
```

- Upload a file with the form field name `audio`.
- The uploaded audio is compared to `reference_audio/reference.wav` using SpeechBrain.

Example curl:

```bash
curl -X POST "http://127.0.0.1:8000/voice-check" \
  -F "audio=@/path/to/audio.wav"
```

### Unified Risk Score

```
POST /risk-score
```

Request body:

```json
{
  "face_score": 0.89,
  "voice_score": 0.42
}
```

Example curl:

```bash
curl -X POST "http://127.0.0.1:8000/risk-score" \
  -H "Content-Type: application/json" \
  -d "{\"face_score\": 0.89, \"voice_score\": 0.42}"
```

## Notes

- Face verification uses DeepFace with the Facenet model and the OpenCV detector.
- Voice verification uses SpeechBrain speaker recognition with cosine similarity.
- Uploaded files are saved in the `uploads/` folder.

## Risk Fusion

- The API uses weighted fusion: `(face_score * 0.6) + (voice_score * 0.4)`.
- SAFE if score >= 0.8, SUSPICIOUS if score >= 0.5, otherwise FRAUD.

## DeepFace Setup

1. Place your reference image at `backend/reference_faces/reference.jpg`.
2. Install dependencies from `requirements.txt`.
3. Start the server and call `POST /face-check` with an image file.

## SpeechBrain Setup

1. Place your reference audio at `backend/reference_audio/reference.wav`.
2. Use WAV files (mono is recommended).
3. Start the server and call `POST /voice-check` with an audio file.
