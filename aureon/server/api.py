import asyncio
import io
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from contextlib import asynccontextmanager
from aureon.config import settings
from aureon.orchestrator import Orchestrator
from aureon.voice.tts_engine import TTSEngine, clean_text_for_speech
from aureon.scheduler.task_scheduler import TaskScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("aureon.server")

orchestrator = Orchestrator()
tts_engine = TTSEngine()
scheduler = TaskScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AUREON services...")
    scheduler.start()
    yield
    logger.info("Shutting down AUREON services...")
    scheduler.stop()

app = FastAPI(
    title="AUREON System Intelligence",
    description="Autonomous Local Voice & System Assistant Backend",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()
tts_engine = TTSEngine()

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True, parents=True)

class ChatRequest(BaseModel):
    message: str
    confirmed_action: Optional[Dict[str, Any]] = None

class ConfirmationRequest(BaseModel):
    confirmed: bool
    action: Dict[str, Any]

@app.get("/api/status")
async def get_status():
    backend = await orchestrator.router.get_active_backend()
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()

    return {
        "status": "operational",
        "assistant_name": "AUREON",
        "active_backend": backend,
        "telemetry": {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_gb": round(mem.used / (1024 ** 3), 2),
            "memory_total_gb": round(mem.total / (1024 ** 3), 2)
        }
    }

@app.post("/api/chat")
async def post_chat(req: ChatRequest):
    try:
        resp = await orchestrator.process_user_input(
            user_input=req.message,
            confirmed_action=req.confirmed_action
        )
        return resp.to_dict()
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/confirm")
async def post_confirm(req: ConfirmationRequest):
    if not req.confirmed:
        return {
            "text": "Destructive operation cancelled by user.",
            "voice_text": "Operation cancelled.",
            "backend_used": "safety_manager",
            "tool_results": [],
            "pending_confirmation": None
        }

    resp = await orchestrator.process_user_input(
        user_input="",
        confirmed_action=req.action
    )
    return resp.to_dict()

@app.get("/api/tts")
async def get_tts(text: str):
    try:
        audio_bytes = await tts_engine.synthesize(text)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"TTS synthesis error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

@app.get("/api/memory")
async def get_memory():
    profile = orchestrator.memory.load_profile()
    ledger = orchestrator.memory.read_ledger(50)
    return {
        "profile": profile,
        "ledger": ledger
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected.")

    # Background task to stream live system telemetry every 2 seconds
    async def telemetry_loop():
        try:
            while True:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                await websocket.send_json({
                    "type": "telemetry",
                    "data": {
                        "cpu": cpu,
                        "ram": mem.percent
                    }
                })
                await asyncio.sleep(2.0)
        except Exception:
            pass

    telemetry_task = asyncio.create_task(telemetry_loop())

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            msg_type = data.get("type", "chat")

            if msg_type == "chat":
                user_msg = data.get("message", "")
                resp = await orchestrator.process_user_input(user_msg)
                await websocket.send_json({
                    "type": "response",
                    "payload": resp.to_dict()
                })
            elif msg_type == "confirm":
                confirmed = data.get("confirmed", False)
                action = data.get("action", {})
                if confirmed:
                    resp = await orchestrator.process_user_input("", confirmed_action=action)
                else:
                    resp = await orchestrator.process_user_input("cancel")
                await websocket.send_json({
                    "type": "response",
                    "payload": resp.to_dict()
                })
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
    finally:
        telemetry_task.cancel()

SCREENSHOT_DIR = settings.data_dir / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True, parents=True)
app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOT_DIR)), name="screenshots")

# Mount Static Files for the Cybernetic HUD
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
