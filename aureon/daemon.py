import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import time
import queue
import re
import asyncio
import winsound
import logging
from typing import Optional
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import pyttsx3
from aureon.orchestrator import Orchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aureon.daemon")

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024
CHANNELS = 1
ENERGY_THRESHOLD = 450
SILENCE_DURATION = 1.0

class AureonDaemon:
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.recognizer = sr.Recognizer()
        self.audio_queue = queue.Queue()
        self.running = True

        self.tts = pyttsx3.init()
        self.tts.setProperty("rate", 185)
        voices = self.tts.getProperty("voices")
        for v in voices:
            if "david" in v.name.lower() or "zira" in v.name.lower():
                self.tts.setProperty("voice", v.id)
                break

    def play_wake_chime(self):
        try:
            winsound.Beep(988, 70)
            winsound.Beep(1318, 110)
        except Exception:
            pass

    def play_standby_chime(self):
        try:
            winsound.Beep(1318, 70)
            winsound.Beep(880, 110)
        except Exception:
            pass

    def speak(self, text: str):
        if not text:
            return
        logger.info(f"Aureon Speaking: {text}")
        try:
            self.tts.say(text)
            self.tts.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.debug(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))

    def record_utterance(self, timeout: float = 8.0) -> Optional[sr.AudioData]:
        frames = []
        is_speaking = False
        silence_start = None
        start_time = time.time()

        while self.running:
            if time.time() - start_time > timeout and not is_speaking:
                return None

            try:
                block = self.audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            audio_data = np.frombuffer(block, dtype=np.int16)
            energy = np.abs(audio_data).mean()

            if energy > ENERGY_THRESHOLD:
                is_speaking = True
                silence_start = None
                frames.append(block)
            elif is_speaking:
                frames.append(block)
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > SILENCE_DURATION:
                    break

        if not frames:
            return None

        raw_bytes = b"".join(frames)
        return sr.AudioData(raw_bytes, SAMPLE_RATE, 2)

    def transcribe(self, audio_data: sr.AudioData) -> str:
        try:
            return self.recognizer.recognize_google(audio_data).strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            logger.warning(f"Google speech recognition network error: {e}")
            return ""

    async def handle_command(self, command: str):
        logger.info(f"Processing command: '{command}'")
        resp = await self.orchestrator.process_user_input(command)
        voice_response = resp.voice_text
        if voice_response:
            self.speak(voice_response)

    def run(self):
        print("=" * 60)
        print("  AUREON BACKGROUND VOICE DAEMON ACTIVE")
        print("  Say 'Hey Aureon' or 'Aureon' from anywhere to speak.")
        print("  Say 'Proceed Aureon' or 'Stop' to dismiss.")
        print("=" * 60)

        self.play_wake_chime()
        self.speak("Aureon online. Ready for your command.")

        with sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            dtype="int16",
            channels=CHANNELS,
            callback=self.audio_callback
        ):
            while self.running:
                audio = self.record_utterance(timeout=60.0)
                if not audio:
                    continue

                text = self.transcribe(audio)
                if not text:
                    continue

                lower_text = text.lower()
                logger.info(f"Heard: '{text}'")

                wake_match = re.search(r"\b(hey\s+aureon|aureon|hi\s+aureon|ok\s+aureon)\b", lower_text)
                if wake_match:
                    self.play_wake_chime()

                    command = re.sub(r"^.*?\b(hey\s+aureon|aureon|hi\s+aureon|ok\s+aureon)\b\s*", "", text, flags=re.IGNORECASE).strip()

                    if re.search(r"\b(proceed|stop|dismiss|cancel|thank you)\b", command, re.IGNORECASE):
                        self.play_standby_chime()
                        self.speak("Standing by.")
                        continue

                    if not command:
                        self.speak("Yes?")
                        follow_up_audio = self.record_utterance(timeout=6.0)
                        if follow_up_audio:
                            command = self.transcribe(follow_up_audio)

                    if command:
                        if re.search(r"\b(proceed|stop|dismiss|cancel|thank you)\b", command, re.IGNORECASE):
                            self.play_standby_chime()
                            self.speak("Standing by.")
                            continue

                        asyncio.run(self.handle_command(command))

if __name__ == "__main__":
    daemon = AureonDaemon()
    try:
        daemon.run()
    except KeyboardInterrupt:
        print("\nAureon Daemon stopped.")
