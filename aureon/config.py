import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

class AureonSettings(BaseModel):
    # Gemini Settings (Primary Cloud Brain)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # NVIDIA Nemotron Settings
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    nemotron_endpoint: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    nemotron_model: str = os.getenv("NEMOTRON_MODEL", "nvidia/nemotron-3-8b-chat")
    nemotron_rpm_limit: int = 40

    # Ollama Settings (Local Fallback)
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "mistral")

    # Server Settings
    host: str = os.getenv("AUREON_HOST", "0.0.0.0")
    port: int = int(os.getenv("AUREON_PORT", "8000"))

    # Voice / TTS Settings
    tts_voice: str = os.getenv("TTS_VOICE", "en-US-GuyNeural")
    tts_rate: str = os.getenv("TTS_RATE", "+0%")
    tts_pitch: str = os.getenv("TTS_PITCH", "+0Hz")

    # Safety
    require_destructive_confirmation: bool = os.getenv("REQUIRE_DESTRUCTIVE_CONFIRMATION", "true").lower() == "true"

    # Paths
    data_dir: Path = DATA_DIR
    profile_file: Path = DATA_DIR / "user_profile.json"
    memory_ledger_file: Path = DATA_DIR / "memory_ledger.md"
    active_tasks_file: Path = DATA_DIR / "active_tasks.json"

settings = AureonSettings()
