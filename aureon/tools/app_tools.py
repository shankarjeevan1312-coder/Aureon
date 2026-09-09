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
            description="Launch an installed desktop application (e.g. notepad, calc, code, chrome, mspaint).",
            is_destructive=False
        )

    async def execute(self, app_name: str, **kwargs) -> ToolResult:
        known_apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "paint": "mspaint.exe",
            "mspaint": "mspaint.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "code": "code",
            "chrome": "chrome",
            "edge": "msedge"
        }

        target = known_apps.get(app_name.lower(), app_name)
        try:
            # Launch without blocking
            subprocess.Popen(target, shell=True)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Application '{app_name}' launched.",
                voice_summary=f"Launching {app_name}."
            )
        except Exception as e:
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
                # Ignore hidden and system dirs
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
            return ToolResult(tool_name=self.name, success=False, output=str(e), voice_summary="File search error.")

registry.register(LaunchAppTool())
registry.register(OpenUrlTool())
registry.register(SearchFilesTool())
