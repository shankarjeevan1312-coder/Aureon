import os
import shutil
import subprocess
import asyncio
import psutil
from typing import Optional, Dict, Any
from aureon.tools.base import BaseTool, ToolResult, registry

class GetSystemStatusTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="get_system_status",
            description="Retrieve real-time telemetry: CPU usage, memory consumption, and disk status.",
            is_destructive=False
        )

    async def execute(self, **kwargs) -> ToolResult:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")

        output = {
            "cpu_percent": cpu_percent,
            "memory_percent": mem.percent,
            "memory_used_gb": round(mem.used / (1024 ** 3), 2),
            "memory_total_gb": round(mem.total / (1024 ** 3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024 ** 3), 2)
        }

        voice = (
            f"CPU is at {cpu_percent} percent. "
            f"Memory usage is at {mem.percent} percent with {round(mem.available / (1024 ** 3), 1)} gigabytes free."
        )

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=output,
            voice_summary=voice
        )

class RunPowerShellTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="run_powershell",
            description="Execute a PowerShell command on the host Windows machine.",
            is_destructive=False
        )

    async def execute(self, command: str, **kwargs) -> ToolResult:
        # Check for dangerous command tokens
        dangerous_tokens = ["rmdir", "remove-item", "format-", "shutdown", "stop-computer", "restart-computer", "stop-process"]
        cmd_lower = command.lower()
        if any(token in cmd_lower for token in dangerous_tokens):
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=f"PowerShell command contains sensitive or destructive operations: '{command}'",
                requires_confirmation=True,
                confirmation_prompt=f"This PowerShell command contains potentially destructive instructions: `{command}`. Confirm execution? (Yes/No)",
                voice_summary="Confirmation required before running this system command."
            )

        try:
            proc = await asyncio.create_subprocess_shell(
                f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"{command}\"",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=20.0)

            out_text = stdout.decode("utf-8", errors="replace").strip()
            err_text = stderr.decode("utf-8", errors="replace").strip()

            success = proc.returncode == 0
            res = out_text if success else f"Error (code {proc.returncode}): {err_text}"
            return ToolResult(
                tool_name=self.name,
                success=success,
                output=res,
                voice_summary="Command executed successfully." if success else "Command returned an error."
            )
        except asyncio.TimeoutError:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="PowerShell command execution timed out after 20 seconds.",
                voice_summary="Command timed out."
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=str(e),
                voice_summary="Execution failed."
            )

class ReadFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read the contents of a local file.",
            is_destructive=False
        )

    async def execute(self, path: str, max_lines: int = 100, **kwargs) -> ToolResult:
        try:
            if not os.path.exists(path):
                return ToolResult(tool_name=self.name, success=False, output=f"File not found: {path}", voice_summary="File not found.")
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = [f.readline() for _ in range(max_lines)]
                content = "".join(lines)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=content,
                voice_summary=f"Read {len(lines)} lines from the requested file."
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=str(e), voice_summary="Failed to read file.")

class DeleteFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="delete_file",
            description="Permanently delete a file or directory. Requires explicit confirmation.",
            is_destructive=True,
            requires_confirmation=True
        )

    async def execute(self, path: str, **kwargs) -> ToolResult:
        try:
            if not os.path.exists(path):
                return ToolResult(tool_name=self.name, success=False, output=f"Path not found: {path}", voice_summary="Target file does not exist.")

            if os.path.isdir(path):
                shutil.rmtree(path)
                msg = f"Deleted directory: {path}"
            else:
                os.remove(path)
                msg = f"Deleted file: {path}"

            return ToolResult(tool_name=self.name, success=True, output=msg, voice_summary="File deleted.")
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=str(e), voice_summary="Deletion failed.")

class KillProcessTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="kill_process",
            description="Terminate a running process by name or PID. Requires explicit confirmation.",
            is_destructive=True,
            requires_confirmation=True
        )

    async def execute(self, pid: Optional[int] = None, name: Optional[str] = None, **kwargs) -> ToolResult:
        terminated = []
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if (pid and proc.info['pid'] == pid) or (name and name.lower() in proc.info['name'].lower()):
                    proc.kill()
                    terminated.append(f"{proc.info['name']} (PID: {proc.info['pid']})")

            if not terminated:
                return ToolResult(tool_name=self.name, success=False, output="No matching process found.", voice_summary="Process not found.")

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Terminated processes: {', '.join(terminated)}",
                voice_summary="Process terminated."
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=str(e), voice_summary="Failed to terminate process.")

# Register system tools
registry.register(GetSystemStatusTool())
registry.register(RunPowerShellTool())
registry.register(ReadFileTool())
registry.register(DeleteFileTool())
registry.register(KillProcessTool())
