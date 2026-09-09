import re
import asyncio
import io
from typing import Optional
import edge_tts
from aureon.config import settings

def clean_text_for_speech(text: str) -> str:
    """
    Sanitizes text according to Section 4.1 of the Master Prompt:
    - Strips code blocks and backticks
    - Strips tool invocation syntax [TOOL: ...]
    - Replaces URLs and local paths with conversational descriptions
    - Replaces technical symbols with spoken equivalents
    """
    if not text:
        return ""

    # Remove tool calls like [TOOL: ...] [ARGS: ...] [CONFIRM: ...]
    text = re.sub(r"\[TOOL:[^\]]+\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[ARGS:[^\]]+\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[CONFIRM:[^\]]+\]", "", text, flags=re.IGNORECASE)

    # Remove markdown code blocks
    text = re.sub(r"```[\s\S]*?```", "I've sent the code to your interface.", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Replace URLs
    text = re.sub(r"https?://\S+", "the requested link", text)

    # Replace Windows / Unix file paths
    text = re.sub(r"[A-Za-z]:\\[^ \n\r\t]+", "the file path", text)
    text = re.sub(r"/[a-zA-Z0-9_\-\./]+", "the system path", text)

    # Replace email addresses with phonetic representation (Section 4.1)
    def spoken_email(match):
        return match.group(0).replace("@", " at ").replace(".", " dot ")
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", spoken_email, text)

    # Collapse repeated whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

class TTSEngine:
    def __init__(self, voice: Optional[str] = None):
        self.voice = voice or settings.tts_voice
        self.rate = settings.tts_rate
        self.pitch = settings.tts_pitch

    async def synthesize(self, text: str) -> bytes:
        clean_text = clean_text_for_speech(text)
        if not clean_text:
            return b""

        communicate = edge_tts.Communicate(
            clean_text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch
        )
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])

        return bytes(audio_data)

    async def save_to_file(self, text: str, output_path: str):
        clean_text = clean_text_for_speech(text)
        if not clean_text:
            return
        communicate = edge_tts.Communicate(
            clean_text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch
        )
        await communicate.save(output_path)
