from SinisterSixSystems.orchestration.orchestrator import Orchestrator
from SinisterSixSystems.entity import AudioRequest, ChatRequest
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from SinisterSixSystems.logging import logger
from fastapi.middleware.cors import CORSMiddleware


from SinisterSixSystems.orchestration.latext_chain import run_task

from langgraph.graph import StateGraph, START, END
from SinisterSixSystems.utils import sanitze_filename
from src.SinisterSixSystems.orchestration.state import AgentState
from SinisterSixSystems.orchestration.audio_agent import AudioAgent

import os
import re
import subprocess


app = FastAPI(title="SinisterSix")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",   # your frontend
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()
orchestrator_workflow = orchestrator.compile()


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        logger.info(f"Received chat request: {req}")

        if req.document != "":
            logger.info("Using provided document for context.")
            response = orchestrator_workflow.invoke({"messages": [HumanMessage(content=req.query)], "document": req.document})
        else:
            logger.info("No document provided, proceeding without context.")
            response = orchestrator_workflow.invoke({"messages": [HumanMessage(content=req.query)], "document": ""})
                
        #await run_task(req.query, filepath=f"./artifacts/processed_files/{sanitze_filename(req.query)}/")

        subprocess.run(["cp", "-r", f"./artifacts/processed_files/{sanitze_filename(req.query)}/", "/mnt/2028B41628B3E944/Projects/eduflow-ai/public/artifacts/processed_files/"])
        
        return {"response": f"Generated Successfully!"}
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/audio")
async def audio_chat(req: AudioRequest):
    try:
        logger.info(f"Received audio chat request: {req}")

        audio_agent = AudioAgent()
        initial_state = {
            "transcript": [],
            "mode": req.mode,
            "markdown_document": open(os.path.join("./artifacts/processed_files/", sanitze_filename(req.query), "processed_document.md"), "r", encoding="utf-8").read(),
            "filepath": os.path.join("./artifacts/processed_files/", sanitze_filename(req.query))
        }
        
        
        audio_agent_worflow = audio_agent.compile()
        response = audio_agent_worflow.invoke(initial_state)

        subprocess.run(["cp", "-r", f"./artifacts/processed_files/{sanitze_filename(req.query)}/audios", f"/mnt/2028B41628B3E944/Projects/eduflow-ai/public/artifacts/processed_files/{sanitze_filename(req.query)}"])

        logger.info(f"Generated audio response")
        return {"response": "Audio Generated Successfully!"}
        
    except Exception as e:
        logger.error(f"Error processing audio chat request: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/")
def root():
    return {"message": "FinConnect Chatbot API is running 🚀"}