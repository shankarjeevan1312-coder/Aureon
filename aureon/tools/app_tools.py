import os
import subprocess
import webbrowser
import fnmatch
from pathlib import Path
from typing import List, Dict, Any
from aureon.tools.base import BaseTool, ToolResult, registry

class LaunchAppTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="launch_app",
            description="Launch an installed desktop application (e.g. whatsapp, spotify, notepad, calc, code, chrome, mspaint).",
            is_destructive=False
        )

    async def execute(self, app_name: str, **kwargs) -> ToolResult:
        clean_name = app_name.lower().strip()

        # Protocol handlers & common executables
        app_map = {
            "whatsapp": "whatsapp:",
            "spotify": "spotify:",
            "discord": "discord:",
            "telegram": "tg:",
            "teams": "msteams:",
            "settings": "ms-settings:",
            "store": "ms-windows-store:",
            "camera": "microsoft.windows.camera:",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "notepad": "notepad.exe",
            "paint": "mspaint.exe",
            "mspaint": "mspaint.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "code": "code",
            "vs code": "code",
            "vscode": "code",
            "chrome": "chrome",
            "google chrome": "chrome",
            "edge": "msedge",
            "microsoft edge": "msedge"
        }

        target = app_map.get(clean_name, clean_name)

        try:
            # On Windows, 'start "" <target>' opens executables, shortcuts, and URI protocols (like whatsapp:)
            if target.endswith(":") or clean_name in ["whatsapp", "spotify", "discord"]:
                subprocess.Popen(f'powershell.exe -NoProfile -Command "Start-Process \'{target}\'"', shell=True)
            else:
                subprocess.Popen(f'start "" "{target}"', shell=True)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Application '{app_name}' launched.",
                voice_summary=f"Launching {app_name}."
            )
        except Exception as e:
            # Fallback for web apps like WhatsApp
            if clean_name == "whatsapp":
                webbrowser.open("https://web.whatsapp.com")
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output="Opened WhatsApp Web in browser.",
                    voice_summary="Opening WhatsApp in your browser."
                )

            return ToolResult(
                tool_name=self.name,
                success=False,
                output=str(e),
                voice_summary=f"Unable to launch {app_name}."
            )

class OpenUrlTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="open_url",
            description="Open a web address or search query in the user's default browser.",
            is_destructive=False
        )

    async def execute(self, url: str, **kwargs) -> ToolResult:
        try:
            if not (url.startswith("http://") or url.startswith("https://")):
                url = f"https://www.google.com/search?q={url}"
            webbrowser.open(url)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Opened in browser: {url}",
                voice_summary="I'll open that in your browser."
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=str(e), voice_summary="Failed to open browser.")

class SearchFilesTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="search_files",
            description="Locate files across user directories by filename pattern.",
            is_destructive=False
        )

    async def execute(self, pattern: str, search_dir: str = "", max_results: int = 15, **kwargs) -> ToolResult:
        if not search_dir:
            search_dir = str(Path.home())

        matches = []
        try:
            for root, dirs, files in os.walk(search_dir):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["AppData", "node_modules", ".git"]]
                for filename in fnmatch.filter(files, f"*{pattern}*"):
                    matches.append(os.path.join(root, filename))
                    if len(matches) >= max_results:
                        break
                if len(matches) >= max_results:
                    break

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=matches,
                voice_summary=f"Found {len(matches)} matching files." if matches else "No matching files found."
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=str(e), voice_summary="Error occurred searching files.")

registry.register(LaunchAppTool())
registry.register(OpenUrlTool())
registry.register(SearchFilesTool())
