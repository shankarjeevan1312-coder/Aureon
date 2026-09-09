import time
import httpx
from typing import List, Dict, Any, Optional
from aureon.config import settings

class NemotronClient:
    """
    Client for NVIDIA Nemotron API.
    Uses OpenAI-compatible chat completion payload.
    Enforces the 40 requests/minute free-tier rate limit.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.nvidia_api_key
        self.endpoint = settings.nemotron_endpoint
        self.model = settings.nemotron_model
        self.request_timestamps: List[float] = []

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("nvapi-your-key"))

    def _check_rate_limit(self) -> bool:
        now = time.time()
        # Keep timestamps from the last 60 seconds
        self.request_timestamps = [t for t in self.request_timestamps if now - t < 60]
        return len(self.request_timestamps) < settings.nemotron_rpm_limit

    async def generate_response(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 1024) -> str:
        if not self.is_configured():
            raise ValueError("NVIDIA API Key is missing or unconfigured.")

        if not self._check_rate_limit():
            raise RuntimeError("Nemotron 40 RPM rate limit reached. Waiting for next window.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.endpoint, headers=headers, json=payload)
            self.request_timestamps.append(time.time())

            if resp.status_code != 200:
                raise RuntimeError(f"Nemotron API returned HTTP {resp.status_code}: {resp.text}")

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError("Nemotron returned no choices in response.")

            return choices[0].get("message", {}).get("content", "").strip()
