import os
import re
import json
import subprocess
import webbrowser
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Optional
from aureon.tools.base import BaseTool, ToolResult, registry

COMMON_WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://www.github.com",
    "chatgpt": "https://chatgpt.com",
    "gemini": "https://gemini.google.com",
    "reddit": "https://www.reddit.com",
    "netflix": "https://www.netflix.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "gmail": "https://mail.google.com",
    "amazon": "https://www.amazon.com",
    "facebook": "https://www.facebook.com",
    "discord web": "https://discord.com/app",
    "whatsapp web": "https://web.whatsapp.com",
    "leetcode": "https://leetcode.com",
    "stackoverflow": "https://stackoverflow.com",
    "huggingface": "https://huggingface.co"
}

class LaunchAppTool(BaseTool):
    """
    Universal App & Web Launcher for Windows:
    1. Scans and launches ANY installed Windows application (Win32, Store, UWP).
    2. Opens ANY website or browser query.
    """
    def __init__(self):
        super().__init__(
            name="launch_app",
            description="Launch ANY application installed on the PC or open ANY website in browser.",
            is_destructive=False
        )
        self._installed_apps_cache: Dict[str, str] = {}
        self._refresh_installed_apps()

    def _refresh_installed_apps(self):
        """Scans Windows Get-StartApps to index every installed app on the PC."""
        try:
            cmd = "Get-StartApps | ConvertTo-Json"
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=5.0
            )
            if proc.returncode == 0 and proc.stdout.strip():
                data = json.loads(proc.stdout)
                if isinstance(data, list):
                    for item in data:
                        name = item.get("Name", "").strip().lower()
                        app_id = item.get("AppID", "").strip()
                        if name and app_id:
                            self._installed_apps_cache[name] = app_id
                elif isinstance(data, dict):
                    name = data.get("Name", "").strip().lower()
                    app_id = data.get("AppID", "").strip()
                    if name and app_id:
                        self._installed_apps_cache[name] = app_id
        except Exception:
            pass

    def _find_installed_app(self, query: str) -> Optional[str]:
        q = query.lower().strip()
        # 1. Exact match
        if q in self._installed_apps_cache:
            return self._installed_apps_cache[q]

        # 2. Prefix / Substring match (e.g. "code" -> "visual studio code")
        for name, app_id in self._installed_apps_cache.items():
            if q == name or q in name or name in q:
                return app_id

        # 3. Word token matching
        tokens = q.split()
        for name, app_id in self._installed_apps_cache.items():
            if any(t in name for t in tokens if len(t) > 2):
                return app_id

        return None

    async def execute(self, app_name: str, **kwargs) -> ToolResult:
        clean = app_name.lower().strip()

        # Check if the user is asking for a known website or web URL
        if clean in COMMON_WEBSITES:
            url = COMMON_WEBSITES[clean]
            webbrowser.open(url)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Opened {clean} in default browser ({url}).",
                voice_summary=f"Opening {clean} in your browser."
            )

        if clean.startswith("http://") or clean.startswith("https://") or re.search(r"\.(com|org|net|io|co|in|edu|gov)$", clean):
            url = clean if clean.startswith("http") else f"https://{clean}"
            webbrowser.open(url)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Opened website: {url}",
                voice_summary=f"Opening {clean} in your browser."
            )

        # Look up installed app in Windows StartApps index
        app_id = self._find_installed_app(clean)
        if app_id:
            try:
                # Launch via Windows shell:AppsFolder protocol (works for all Win32 and UWP Store apps)
                subprocess.Popen(
                    f'powershell.exe -NoProfile -Command "Start-Process \'shell:AppsFolder\\{app_id}\'"',
                    shell=True
                )
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=f"Launched application '{app_name}' (AppID: {app_id}).",
                    voice_summary=f"Launching {app_name}."
                )
            except Exception as e:
                pass

        # Try standard Windows 'start' command for direct executables or protocols
        try:
            subprocess.Popen(f'start "" "{clean}"', shell=True)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Launched '{app_name}' via Windows system.",
                voice_summary=f"Opening {app_name}."
            )
        except Exception:
            pass

        # If not installed, fallback to opening as a web search / website
        fallback_url = f"https://www.google.com/search?q={clean}"
        webbrowser.open(fallback_url)
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"'{app_name}' not found locally. Opened search in browser: {fallback_url}",
            voice_summary=f"Searching for {app_name} in your browser."
        )

class OpenUrlTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="open_url",
            description="Open any web address, website, or search query in the default browser.",
            is_destructive=False
        )

    async def execute(self, url: str, **kwargs) -> ToolResult:
        clean = url.strip()
        try:
            if clean.lower() in COMMON_WEBSITES:
                final_url = COMMON_WEBSITES[clean.lower()]
            elif clean.startswith("http://") or clean.startswith("https://"):
                final_url = clean
            elif re.search(r"^[a-zA-Z0-9\-]+(\.[a-zA-Z]{2,})", clean):
                final_url = f"https://{clean}"
            else:
                final_url = f"https://www.google.com/search?q={clean}"

            webbrowser.open(final_url)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Opened in browser: {final_url}",
                voice_summary="Opening that in your browser."
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
