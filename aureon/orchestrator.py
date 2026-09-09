import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from aureon.config import settings
from aureon.llm.router import LLMRouter
from aureon.memory.memory_manager import MemoryManager
from aureon.tools.base import registry, ToolResult
from aureon.voice.tts_engine import clean_text_for_speech

logger = logging.getLogger("aureon.orchestrator")

MASTER_SYSTEM_PROMPT = """You are AUREON: an advanced autonomous voice-driven operating intelligence.
Tone: Composed, concise, articulate, calm, effortlessly efficient.
Purpose: Primary digital operator on Windows. Execute commands, manage communications, maintain persistent context.

Persona & Output Guidelines:
- Speak with the precision of a high-grade operating assistant. Avoid robotic clichés.
- Brevity Rule: 1 to 3 sentences maximum for routine verbal responses.
- When performing system actions, output the structured tool call strictly in this format:
[TOOL: <tool_name>]
[ARGS: {<json_arguments>}]
[CONFIRM: yes/no]

Available Tools:
- get_system_status: Retrieve CPU, RAM, Disk statistics.
- get_battery_status: Inspect battery percentage and charging state.
- get_network_info: Inspect local IP address and network metrics.
- volume_control(action="set"|"mute"|"unmute", level=0-100): Control system sound volume.
- capture_screenshot: Capture primary screen and save image.
- clipboard_read: Read system clipboard text.
- clipboard_write(text="..."): Copy text to clipboard.
- list_active_windows: List open foreground windows and application titles.
- run_powershell(command="..."): Execute PowerShell command on host.
- read_file(path="..."): Read file content.
- write_file(path="...", content="...", append=False): Create or write file content.
- delete_file(path="..."): Permanently delete file/folder (REQUIRES CONFIRMATION: yes).
- kill_process(name="..." or pid=...): Terminate running process (REQUIRES CONFIRMATION: yes).
- launch_app(app_name="..."): Launch desktop application (e.g. notepad, calc, code, chrome).
- open_url(url="..."): Open browser URL or search web.
- search_files(pattern="..."): Search files on system.
- send_email(to="...", subject="...", body="..."): Send email (REQUIRES CONFIRMATION: yes).
- create_task_reminder(title="...", due_time="..."): Add task to memory ledger.

Always confirm destructive operations. Follow up tool execution with a brief, clear sentence.
"""

class OrchestratorResponse:
    def __init__(
        self,
        text: str,
        voice_text: str,
        backend_used: str,
        tool_results: List[ToolResult] = None,
        pending_confirmation: Optional[Dict[str, Any]] = None
    ):
        self.text = text
        self.voice_text = voice_text
        self.backend_used = backend_used
        self.tool_results = tool_results or []
        self.pending_confirmation = pending_confirmation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "voice_text": self.voice_text,
            "backend_used": self.backend_used,
            "tool_results": [t.model_dump() for t in self.tool_results],
            "pending_confirmation": self.pending_confirmation
        }

class Orchestrator:
    def __init__(self):
        self.router = LLMRouter()
        self.memory = MemoryManager()
        self.conversation_history: List[Dict[str, str]] = []

    def _build_messages(self, user_input: str) -> List[Dict[str, str]]:
        context = self.memory.get_context_summary()
        sys_content = f"{MASTER_SYSTEM_PROMPT}\n\n[PERSISTENT CONTEXT]\n{context}"

        messages = [{"role": "system", "content": sys_content}]
        # Include recent history (last 6 turns)
        messages.extend(self.conversation_history[-6:])
        messages.append({"role": "user", "content": user_input})
        return messages

    def _parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        tool_match = re.search(r"\[TOOL:\s*([^\]]+)\]", text, re.IGNORECASE)
        args_match = re.search(r"\[ARGS:\s*(\{.*?\})\]", text, re.DOTALL | re.IGNORECASE)
        confirm_match = re.search(r"\[CONFIRM:\s*([^\]]+)\]", text, re.IGNORECASE)

        if tool_match:
            tool_name = tool_match.group(1).strip()
            args = {}
            if args_match:
                try:
                    args = json.loads(args_match.group(1).strip())
                except Exception as e:
                    logger.warning(f"Failed to parse tool args JSON: {e}")

            confirm_str = confirm_match.group(1).strip().lower() if confirm_match else "no"
            requires_confirm = confirm_str.startswith("yes")

            return {
                "name": tool_name,
                "args": args,
                "declared_confirm": requires_confirm
            }
        return None

    async def process_user_input(self, user_input: str, confirmed_action: Optional[Dict[str, Any]] = None) -> OrchestratorResponse:
        # 1. Handle Explicit Memory Triggers
        lower_input = user_input.lower().strip()
        if lower_input.startswith("remember that ") or lower_input.startswith("remember "):
            fact = re.sub(r"^remember\s+(that\s+)?", "", user_input, flags=re.IGNORECASE).strip()
            self.memory.add_learned_fact(fact)
            ack = f"Memory updated. Stored: {fact}."
            return OrchestratorResponse(
                text=ack,
                voice_text=ack,
                backend_used="memory_engine"
            )

        # 2. Handle Confirmed Action Execution if resuming from approval
        if confirmed_action:
            tool_name = confirmed_action.get("name")
            tool_args = confirmed_action.get("args", {})
            result = await registry.run_tool(tool_name, tool_args, confirmed=True)
            voice_summary = result.voice_summary or "Action completed."
            return OrchestratorResponse(
                text=f"Confirmed action '{tool_name}' executed. Result:\n{result.output}",
                voice_text=voice_summary,
                backend_used="tool_executor",
                tool_results=[result]
            )

        # 3. Query LLM Router
        messages = self._build_messages(user_input)
        raw_response, backend = await self.router.generate(messages)

        # 4. Check for Tool Invocation in Response
        tool_call = self._parse_tool_call(raw_response)
        tool_results: List[ToolResult] = []
        pending_confirmation = None

        if tool_call:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            tool_obj = registry.get_tool(tool_name)
            is_destructive = tool_obj.is_destructive if tool_obj else tool_call["declared_confirm"]

            if is_destructive and settings.require_destructive_confirmation:
                # Quarantine and return pending confirmation request
                pending_confirmation = {
                    "name": tool_name,
                    "args": tool_args,
                    "prompt": f"Destructive operation: '{tool_name}'. Proceed? Target: {json.dumps(tool_args)}"
                }
                voice_text = "This action requires your confirmation before execution."
                display_text = f"{raw_response}\n\n⚠️ Confirmation required to proceed with {tool_name}."
            else:
                # Execute tool immediately
                result = await registry.run_tool(tool_name, tool_args, confirmed=True)
                tool_results.append(result)
                voice_text = result.voice_summary or clean_text_for_speech(raw_response)
                display_text = f"{raw_response}\n\n[Result]: {result.output}"
        else:
            voice_text = clean_text_for_speech(raw_response)
            display_text = raw_response

        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": display_text})

        return OrchestratorResponse(
            text=display_text,
            voice_text=voice_text,
            backend_used=backend,
            tool_results=tool_results,
            pending_confirmation=pending_confirmation
        )
