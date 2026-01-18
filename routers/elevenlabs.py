from dotenv import load_dotenv
load_dotenv()
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import requests
import os

router = APIRouter(prefix="/asr", tags=["ASR"])

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/speech-to-text"

@router.post("/elevenlabs")
async def elevenlabs_transcribe(
    file: UploadFile = File(...),
    model_id: str = Form("scribe_v1")  # REQUIRED
):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Only audio files allowed")

    audio_bytes = await file.read()

    response = requests.post(
        ELEVENLABS_URL,
        headers={
            "xi-api-key": os.environ.get("ELEVENLABS_API_KEY")
        },
        files={
            "file": (file.filename, audio_bytes, file.content_type)
        },
        data={
            "model_id": model_id
        },
        timeout=30
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    return {
        "engine": "elevenlabs",
        "model": model_id,
        "text": response.json().get("text")
    }
