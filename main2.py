from fastapi import FastAPI
# from routers.whisperasr import router as whisper_router
from routers.elevenlabs import router as eleven_router

app = FastAPI(title="ASR Service")

# app.include_router(whisper_router)
app.include_router(eleven_router)
