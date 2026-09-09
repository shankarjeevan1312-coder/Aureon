import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from aureon.config import settings
from aureon.tools.base import BaseTool, ToolResult, registry

SCREENSHOT_DIR = settings.data_dir / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True, parents=True)

class CaptureScreenshotTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="capture_screenshot",
            description="Capture a high-resolution screenshot of the primary display.",
            is_destructive=False
        )

    async def execute(self, **kwargs) -> ToolResult:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = SCREENSHOT_DIR / filename

        safe_path = str(filepath).replace("\\", "/")
        # PowerShell script using Windows .NET Graphics
        ps_script = f"""
        Add-Type -AssemblyName System.Windows.Forms,System.Drawing
        $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bmp)
        $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
        $bmp.Save('{safe_path}', [System.Drawing.Imaging.ImageFormat]::Png)
        $graphics.Dispose()
        $bmp.Dispose()
        """

        try:
            proc = await asyncio.create_subprocess_shell(
                f"powershell.exe -NoProfile -Command \"{ps_script}\"",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

            if filepath.exists():
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output={
                        "path": str(filepath),
                        "filename": filename,
                        "url": f"/screenshots/{filename}"
                    },
                    voice_summary="Screenshot captured and saved."
                )
            else:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="Screenshot file could not be created.",
                    voice_summary="Failed to capture screen."
                )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=str(e),
                voice_summary="Screenshot failed."
            )

class ClipboardReadTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="clipboard_read",
            description="Read the current text contents of the system clipboard.",
            is_destructive=False
        )

    async def execute(self, **kwargs) -> ToolResult:
        try:
            proc = await asyncio.create_subprocess_shell(
                "powershell.exe -NoProfile -Command \"Get-Clipboard\"",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            text = stdout.decode("utf-8", errors="replace").strip()
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=text or "(Clipboard is empty)",
                voice_summary=f"Read {len(text)} characters from clipboard." if text else "Clipboard is empty."
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=str(e), voice_summary="Clipboard read failed.")

class ClipboardWriteTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="clipboard_write",
            description="Copy specified text to the system clipboard.",
            is_destructive=False
        )

    async def execute(self, text: str, **kwargs) -> ToolResult:
        try:
            # Escape double quotes for PowerShell
            escaped = text.replace("\"", "`\"").replace("$", "`$")
            proc = await asyncio.create_subprocess_shell(
                f"powershell.exe -NoProfile -Command \"Set-Clipboard -Value \\\"{escaped}\\\"\"",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return ToolResult(
                tool_name=self.name,
                success=True,
                output="Text successfully copied to clipboard.",
                voice_summary="Copied to your clipboard."
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=str(e), voice_summary="Clipboard write failed.")

class ListActiveWindowsTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="list_active_windows",
            description="List running foreground desktop windows and their titles.",
            is_destructive=False
        )

    async def execute(self, **kwargs) -> ToolResult:
        try:
            ps_cmd = "Get-Process | Where-Object { $_.MainWindowTitle } | Select-Object -Property ProcessName, MainWindowTitle | ConvertTo-Json"
            proc = await asyncio.create_subprocess_shell(
                f"powershell.exe -NoProfile -Command \"{ps_cmd}\"",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            import json
            raw_out = stdout.decode("utf-8", errors="replace").strip()
            windows = json.loads(raw_out) if raw_out else []
            if isinstance(windows, dict):
                windows = [windows]

            titles = [w.get("MainWindowTitle") for w in windows if w.get("MainWindowTitle")]
            summary_voice = f"Found {len(titles)} active windows."
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=windows,
                voice_summary=summary_voice
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=str(e), voice_summary="Failed to list windows.")

class WriteFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="write_file",
            description="Create or overwrite a file at the specified path with content.",
            is_destructive=False
        )

    async def execute(self, path: str, content: str, append: bool = False, **kwargs) -> ToolResult:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with open(p, mode, encoding="utf-8") as f:
                f.write(content)

            verb = "appended to" if append else "written to"
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Successfully {verb} {path} ({len(content)} chars).",
                voice_summary=f"File {verb} successfully."
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=str(e), voice_summary="Failed to write file.")

registry.register(CaptureScreenshotTool())
registry.register(ClipboardReadTool())
registry.register(ClipboardWriteTool())
registry.register(ListActiveWindowsTool())
registry.register(WriteFileTool())
