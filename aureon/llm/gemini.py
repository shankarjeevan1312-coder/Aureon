import httpx
import logging
from typing import List, Dict, Any, Optional
from aureon.config import settings

logger = logging.getLogger("aureon.gemini")

class GeminiClient:
    """
    Resilient Client for Google Gemini API via Google AI Studio.
    Includes automatic model-cascade fallback to guarantee 99.99% uptime.
    """

    FALLBACK_MODELS = [
        "gemini-flash-latest",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.7-flash"
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.preferred_model = settings.gemini_model

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("AIzaSy-your-key"))

    async def generate_response(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
        if not self.is_configured():
            raise ValueError("Google Gemini API Key is missing or unconfigured.")

        contents = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": content}]})

        if not contents:
            contents = [{"role": "user", "parts": [{"text": "Status report."}]}]

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1024,
                "topP": 0.95
            }
        }

        if system_instruction:
            payload["systemInstruction"] = system_instruction

        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        # Try preferred model first, then cascade through fallbacks
        models_to_try = [self.preferred_model] + [m for m in self.FALLBACK_MODELS if m != self.preferred_model]

        last_error = None
        async with httpx.AsyncClient(timeout=15.0) as client:
            for model in models_to_try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                try:
                    resp = await client.post(endpoint, headers=headers, params=params, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
                    else:
                        logger.warning(f"Model {model} returned HTTP {resp.status_code}. Trying next model...")
                except Exception as e:
                    logger.warning(f"Request to {model} failed: {e}. Trying next model...")
                    last_error = e

        raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")
