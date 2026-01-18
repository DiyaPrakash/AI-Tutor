from fastapi import APIRouter, WebSocket
import torch
from faster_whisper import WhisperModel
import numpy as np

router = APIRouter()

model = WhisperModel(
    "large-v2",
    device="cuda" if torch.cuda.is_available() else "cpu",
    compute_type="int8_float16"
)

@router.websocket("/ws/transcribe")
async def whisper_stream(websocket: WebSocket):
    await websocket.accept()
    buffer = bytearray()

    try:
        while True:
            chunk = await websocket.receive_bytes()
            buffer.extend(chunk)

            if len(buffer) > 16000 * 5 * 2:  # ~5s
                audio = np.frombuffer(buffer, dtype=np.int16).astype(np.float32) / 32768
                segments, _ = model.transcribe(audio, language="en")

                text = "".join(seg.text for seg in segments)
                await websocket.send_text(text)
                buffer.clear()

    except Exception:
        await websocket.close()
