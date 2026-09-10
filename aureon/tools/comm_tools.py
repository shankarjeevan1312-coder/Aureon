import json
import urllib.parse
import subprocess
import webbrowser
from typing import Optional, Dict, Any
from aureon.tools.base import BaseTool, ToolResult, registry
from aureon.memory.memory_manager import MemoryManager

memory = MemoryManager()

def launch_protocol(uri: str):
    """Reliably triggers Windows URI protocols (mailto:, whatsapp:, tel:)."""
    try:
        subprocess.Popen(f'powershell.exe -NoProfile -Command "Start-Process \'{uri}\'"', shell=True)
    except Exception:
        webbrowser.open(uri)

class SendWhatsAppTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="send_whatsapp_message",
            description="Send a message to a phone number or contact via WhatsApp. Requires recipient and message text.",
            is_destructive=False
        )

    async def execute(self, recipient: str, message: str, **kwargs) -> ToolResult:
        encoded_msg = urllib.parse.quote(message)
        # Clean phone digits if international number provided
        clean_phone = "".join(c for c in recipient if c.isdigit() or c == "+")

        # Try native WhatsApp protocol first, fallback to web
        if clean_phone:
            target_uri = f"whatsapp://send?phone={clean_phone}&text={encoded_msg}"
            web_fallback = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"
        else:
            target_uri = f"whatsapp://send?text={encoded_msg}"
            web_fallback = f"https://web.whatsapp.com/send?text={encoded_msg}"

        launch_protocol(target_uri)
        memory.log_event("whatsapp_sent", f"Recipient: {recipient} | Msg: {message[:40]}")

        return ToolResult(
            tool_name=self.name,
            success=True,
            output={
                "type": "whatsapp",
                "recipient": recipient,
                "message": message,
                "uri": target_uri,
                "web_url": web_fallback
            },
            voice_summary=f"Opening WhatsApp to send message to {recipient}."
        )

class SendEmailTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="send_email",
            description="Compose and dispatch an email with recipient, subject, and body.",
            is_destructive=False
        )

    async def execute(self, to: str, subject: str, body: str, **kwargs) -> ToolResult:
        encoded_sub = urllib.parse.quote(subject)
        encoded_body = urllib.parse.quote(body)
        mailto_uri = f"mailto:{to}?subject={encoded_sub}&body={encoded_body}"
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={to}&su={encoded_sub}&body={encoded_body}"

        launch_protocol(mailto_uri)
        memory.log_event("email_sent", f"To: {to} | Subject: {subject}")

        return ToolResult(
            tool_name=self.name,
            success=True,
            output={
                "type": "email",
                "to": to,
                "subject": subject,
                "mailto": mailto_uri,
                "gmail_url": gmail_url
            },
            voice_summary=f"Opening email to {to} regarding {subject}."
        )

class MakeCallTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="make_call",
            description="Initiate a voice or phone call to a contact/number via Windows Phone Link or default dialer.",
            is_destructive=False
        )

    async def execute(self, phone: str, **kwargs) -> ToolResult:
        clean_phone = "".join(c for c in phone if c.isdigit() or c in "+*#")
        tel_uri = f"tel:{clean_phone}"
        launch_protocol(tel_uri)
        memory.log_event("call_initiated", f"Target: {phone}")

        return ToolResult(
            tool_name=self.name,
            success=True,
            output={"type": "call", "target": phone, "uri": tel_uri},
            voice_summary=f"Initiating call to {phone}."
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

registry.register(SendWhatsAppTool())
registry.register(SendEmailTool())
registry.register(MakeCallTool())
registry.register(CreateTaskReminderTool())
