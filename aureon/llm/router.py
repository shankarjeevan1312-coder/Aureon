import logging
from typing import List, Dict, Any, Tuple
from aureon.llm.gemini import GeminiClient
from aureon.llm.nemotron import NemotronClient
from aureon.llm.ollama import OllamaClient

logger = logging.getLogger("aureon.router")

class LLMRouter:
    """
    Intelligent LLM Router conforming to Section 2.8 of AUREON Master Spec:
    1. Primary: Google Gemini 2.0 Flash (Fastest, zero-cost, 1M context, no expiration)
    2. Secondary: NVIDIA Nemotron API (40 RPM free tier)
    3. Fallback: Local Ollama (100% offline)
    4. Diagnostic: Built-in local rule-based intent executor
    """

    def __init__(self):
        self.gemini = GeminiClient()
        self.nemotron = NemotronClient()
        self.ollama = OllamaClient()

    async def get_active_backend(self) -> str:
        if self.gemini.is_configured():
            return "gemini"
        if self.nemotron.is_configured():
            return "nemotron"
        if await self.ollama.is_available():
            return "ollama"
        return "diagnostic_mode"

    async def generate(self, messages: List[Dict[str, str]]) -> Tuple[str, str]:
        """
        Returns: (response_text, backend_used)
        """
        # 1. Try Primary: Google Gemini 2.0 Flash
        if self.gemini.is_configured():
            try:
                text = await self.gemini.generate_response(messages)
                return text, "gemini"
            except Exception as e:
                logger.warning(f"Gemini API call failed ({e}). Falling back to Nemotron/Ollama...")

        # 2. Try Secondary: NVIDIA Nemotron API
        if self.nemotron.is_configured():
            try:
                text = await self.nemotron.generate_response(messages)
                return text, "nemotron"
            except Exception as e:
                logger.warning(f"Nemotron API call failed ({e}). Falling back to Ollama...")

        # 3. Try Fallback: Local Ollama
        if await self.ollama.is_available():
            try:
                text = await self.ollama.generate_response(messages)
                return text, "ollama"
            except Exception as e:
                logger.warning(f"Ollama fallback failed ({e}).")

        # 4. Offline Diagnostic / Simulation Mode
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "").lower()
                break

        diagnostic_response = self._diagnostic_fallback(last_user_msg)
        return diagnostic_response, "diagnostic_mode"

    def _diagnostic_fallback(self, query: str) -> str:
        """
        Provides direct execution or clear status when external LLM is not connected.
        """
        if "cpu" in query or "ram" in query or "system status" in query or "telemetry" in query:
            return "[TOOL: get_system_status]\n[ARGS: {}]\n[CONFIRM: no]\nI am checking your current system telemetry now."

        if "battery" in query or "power" in query or "charging" in query:
            return "[TOOL: get_battery_status]\n[ARGS: {}]\n[CONFIRM: no]\nChecking battery telemetry."

        if "network" in query or "ip" in query or "wifi" in query:
            return "[TOOL: get_network_info]\n[ARGS: {}]\n[CONFIRM: no]\nRetrieving network connection information."

        if "screenshot" in query or "screen capture" in query:
            return "[TOOL: capture_screenshot]\n[ARGS: {}]\n[CONFIRM: no]\nCapturing display screenshot now."

        if "volume" in query or "mute" in query:
            if "mute" in query:
                return "[TOOL: volume_control]\n[ARGS: {\"action\": \"mute\"}]\n[CONFIRM: no]\nMuting audio."
            return "[TOOL: volume_control]\n[ARGS: {\"action\": \"set\", \"level\": 50}]\n[CONFIRM: no]\nAdjusting volume."

        if "clipboard" in query:
            return "[TOOL: clipboard_read]\n[ARGS: {}]\n[CONFIRM: no]\nReading clipboard content."

        if "window" in query or "apps open" in query or "active apps" in query:
            return "[TOOL: list_active_windows]\n[ARGS: {}]\n[CONFIRM: no]\nInspecting active desktop windows."

        if "notepad" in query:
            return "[TOOL: launch_app]\n[ARGS: {\"app_name\": \"notepad\"}]\n[CONFIRM: no]\nLaunching Notepad immediately."

        if "github" in query or "username" in query:
            return "System parameters and memory are synchronized."

        if "delete" in query or "remove" in query:
            return "[TOOL: delete_file]\n[ARGS: {\"path\": \"example_file.txt\"}]\n[CONFIRM: yes]\nThis will delete the requested file. This cannot be undone. Confirm? Yes/No"

        return (
            "AUREON operating system active. To enable continuous conversational reasoning, "
            "provide a Google Gemini API key or NVIDIA Nemotron key in your .env file, or start local Ollama."
        )
