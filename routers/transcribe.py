from fastapi import APIRouter, WebSocket
import torch
import numpy as np
from faster_whisper import WhisperModel

router = APIRouter()

model = WhisperModel(
    "large-v2",
    device="cuda" if torch.cuda.is_available() else "cpu",
    compute_type="int8"
)

@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()

            # Convert raw PCM16 → float32
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            segments, _ = model.transcribe(audio_np, language="en")

            text = "".join(seg.text for seg in segments)

            await websocket.send_text(text or "[no speech]")
    except Exception as e:
        print("WebSocket error:", e)
        await websocket.close()
