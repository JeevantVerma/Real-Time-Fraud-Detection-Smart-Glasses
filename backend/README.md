# Real-Time Fraud Detection Smart Glasses - Phase A (Backend)

This backend provides simulated face verification, voice verification, and unified risk scoring APIs.

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

Example curl:

```bash
curl -X POST "http://127.0.0.1:8000/voice-check" \
  -F "audio=@/path/to/audio.wav"
```

### Unified Risk Score

```
GET /risk-score
```

Example curl:

```bash
curl -X GET "http://127.0.0.1:8000/risk-score"
```

## Notes

- This backend simulates results with random scores.
- Uploaded files are saved in the `uploads/` folder.
