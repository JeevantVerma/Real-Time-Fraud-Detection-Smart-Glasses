# Real-Time Fraud Detection Smart Glasses - Phase B (Frontend)

Modern dashboard UI that connects to the FastAPI backend for face, voice, and risk scoring.

## Setup Instructions

1. Open a terminal in the `frontend` folder.
2. Install dependencies:

```bash
npm install
```

## Run the Frontend

```bash
npm run dev
```

The app will be available at `http://127.0.0.1:5173` (Vite default).

## Notes

- Ensure the backend is running at `http://127.0.0.1:8000`.
- The UI sends:
	- `POST /face-check`
	- `POST /voice-check`
	- `GET /risk-score`
