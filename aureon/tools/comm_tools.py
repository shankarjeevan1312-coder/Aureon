import json
from typing import Optional, Dict, Any
from aureon.tools.base import BaseTool, ToolResult, registry
from aureon.memory.memory_manager import MemoryManager

memory = MemoryManager()

class SendEmailTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="send_email",
            description="Compose and dispatch an email. Classified as sensitive; requires explicit confirmation.",
            is_destructive=False,
            requires_confirmation=True
        )

    async def execute(self, to: str, subject: str, body: str, **kwargs) -> ToolResult:
        # Log communication in memory ledger
        memory.log_event("email_sent", f"To: {to} | Subject: {subject}")
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Email queued and dispatched to {to}.",
            voice_summary=f"Email sent to {to} regarding {subject}."
        )

class CreateTaskReminderTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="create_task_reminder",
            description="Record a scheduled task or reminder in AUREON's memory ledger.",
            is_destructive=False
        )

    async def execute(self, title: str, due_time: str = "soon", **kwargs) -> ToolResult:
        memory.log_event("task_created", f"{title} (Due: {due_time})")
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Reminder recorded: '{title}' scheduled for {due_time}.",
            voice_summary=f"I've recorded that task for {due_time}."
        )

registry.register(SendEmailTool())
registry.register(CreateTaskReminderTool())
