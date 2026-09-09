import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from aureon.config import settings

class MemoryManager:
    """
    Manages persistent memory storage for AUREON:
    - user_profile.json (structured user attributes and persistent configuration)
    - memory_ledger.md (chronological log of persistent notes and learned patterns)
    - active_tasks.json (active workflows and system tasks)
    """

    def __init__(self):
        self.profile_path = settings.profile_file
        self.ledger_path = settings.memory_ledger_file
        self.tasks_path = settings.active_tasks_file
        self._init_storage()

    def _init_storage(self):
        # Initialize user_profile.json if not present
        if not self.profile_path.exists():
            default_profile = {
                "user_name": "Revanth",
                "github_username": "revanthbarthu",
                "os": "Windows",
                "assistant_name": "AUREON",
                "tone": "Composed, concise, articulate, calm, effortlessly efficient",
                "preferences": {
                    "audio_enabled": True,
                    "voice": settings.tts_voice,
                    "default_shell": "powershell"
                },
                "learned_facts": [
                    "User's GitHub username is revanthbarthu.",
                    "Primary OS environment is Windows."
                ],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            self.save_profile(default_profile)

        # Initialize memory_ledger.md if not present
        if not self.ledger_path.exists():
            initial_ledger = (
                f"# AUREON Memory Ledger\n"
                f"Initialized: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"## Persistent System & User Facts\n"
                f"- [Core Fact] User GitHub account: revanthbarthu\n"
                f"- [System] Running as AUREON operating intelligence on Windows host\n\n"
                f"## Event Log\n"
            )
            with open(self.ledger_path, "w", encoding="utf-8") as f:
                f.write(initial_ledger)

        # Initialize active_tasks.json if not present
        if not self.tasks_path.exists():
            with open(self.tasks_path, "w", encoding="utf-8") as f:
                json.dump({"active_tasks": [], "history": []}, f, indent=2)

    def load_profile(self) -> Dict[str, Any]:
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_profile(self, data: Dict[str, Any]):
        data["updated_at"] = datetime.now().isoformat()
        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def update_preference(self, key: str, value: Any):
        profile = self.load_profile()
        if "preferences" not in profile:
            profile["preferences"] = {}
        profile["preferences"][key] = value
        self.save_profile(profile)

    def add_learned_fact(self, fact: str):
        profile = self.load_profile()
        facts: List[str] = profile.get("learned_facts", [])
        if fact not in facts:
            facts.append(fact)
            profile["learned_facts"] = facts
            self.save_profile(profile)

        # Append to memory ledger
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"- [{timestamp}] Fact: {fact}\n"
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def log_event(self, event_type: str, description: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"- [{timestamp}] [{event_type.upper()}] {description}\n"
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def read_ledger(self, tail_lines: int = 50) -> str:
        if not self.ledger_path.exists():
            return ""
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return "".join(lines[-tail_lines:])
        except Exception as e:
            return f"Error reading ledger: {e}"

    def get_context_summary(self) -> str:
        """Constructs concise context string to inject into LLM system prompt."""
        profile = self.load_profile()
        user_name = profile.get("user_name", "User")
        github_user = profile.get("github_username", "unknown")
        learned_facts = profile.get("learned_facts", [])

        facts_text = "\n".join([f"- {f}" for f in learned_facts[-10:]])
        return (
            f"User: {user_name} (GitHub: {github_user})\n"
            f"Operating System: Windows\n"
            f"Known Facts & Context:\n{facts_text}"
        )
