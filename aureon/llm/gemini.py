import httpx
from typing import List, Dict, Any, Optional
from aureon.config import settings

class GeminiClient:
    """
    Client for Google Gemini API (Gemini 2.0 Flash via Google AI Studio).
    Provides ultra-fast, zero-cost conversational intelligence with 1M context.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model = settings.gemini_model
        # Google AI Studio Gemini generateContent endpoint
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

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

        headers = {
            "Content-Type": "application/json"
        }

        params = {
            "key": self.api_key
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.endpoint, headers=headers, params=params, json=payload)

            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini returned no response candidates.")

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise RuntimeError("Gemini returned empty parts.")

            return parts[0].get("text", "").strip()
