import os
import re
import json
import subprocess
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
    "discord": "https://discord.com/app",
    "whatsapp web": "https://web.whatsapp.com",
    "leetcode": "https://leetcode.com",
    "stackoverflow": "https://stackoverflow.com",
    "spotify web": "https://open.spotify.com"
}

def open_url_system(url: str):
    """Reliably opens a URL in a new browser tab/window on Windows."""
    try:
        subprocess.Popen(f'powershell.exe -NoProfile -Command "Start-Process \'{url}\'"', shell=True)
    except Exception:
        os.system(f'start "" "{url}"')

class LaunchAppTool(BaseTool):
    """
    Universal App & Web Launcher for Windows:
    1. Opens ANY website or web app in a new browser tab.
    2. Opens ANY installed desktop app from Windows StartApps index.
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

    def _clean_query(self, query: str) -> str:
        q = query.lower().strip()
        # Strip trailing filler words like "app", "application", "desktop", "software"
        q = re.sub(r"\b(app|application|software|program)\b", "", q).strip()
        return q

    def _find_installed_app(self, query: str) -> Optional[str]:
        q = self._clean_query(query)
        if not q:
            return None

        # 1. Exact match
        if q in self._installed_apps_cache:
            return self._installed_apps_cache[q]

        # 2. Substring match
        for name, app_id in self._installed_apps_cache.items():
            if q == name or q in name or name in q:
                return app_id

        # 3. Token match
        tokens = q.split()
        for name, app_id in self._installed_apps_cache.items():
            if any(t in name for t in tokens if len(t) > 2):
                return app_id

        return None

    async def execute(self, app_name: str, **kwargs) -> ToolResult:
        raw_clean = app_name.lower().strip()
        clean = self._clean_query(raw_clean)

        # 1. Check if the user is asking for a known website or web platform
        matched_web = None
        for site_name, site_url in COMMON_WEBSITES.items():
            if clean == site_name or clean in site_name or site_name in clean:
                matched_web = (site_name, site_url)
                break

        if matched_web:
            site_name, site_url = matched_web
            open_url_system(site_url)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={"type": "url", "url": site_url, "name": site_name},
                voice_summary=f"Opening {site_name} in your browser."
            )

        if clean.startswith("http://") or clean.startswith("https://") or re.search(r"\.(com|org|net|io|co|in|edu|gov)$", clean):
            url = clean if clean.startswith("http") else f"https://{clean}"
            open_url_system(url)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={"type": "url", "url": url, "name": clean},
                voice_summary=f"Opening {clean} in your browser."
            )

        # 2. Look up installed app in Windows StartApps index
        app_id = self._find_installed_app(clean)
        if app_id:
            try:
                subprocess.Popen(
                    f'powershell.exe -NoProfile -Command "Start-Process \'shell:AppsFolder\\{app_id}\'"',
                    shell=True
                )
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output={"type": "app", "name": app_name, "app_id": app_id},
                    voice_summary=f"Launching {app_name}."
                )
            except Exception:
                pass

        # 3. Try standard Windows 'start' command for direct executables or protocols
        try:
            subprocess.Popen(f'start "" "{clean}"', shell=True)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={"type": "app", "name": app_name},
                voice_summary=f"Opening {app_name}."
            )
        except Exception:
            pass

        # 4. Fallback: Search in browser
        fallback_url = f"https://www.google.com/search?q={clean}"
        open_url_system(fallback_url)
        return ToolResult(
            tool_name=self.name,
            success=True,
            output={"type": "url", "url": fallback_url, "name": clean},
            voice_summary=f"Searching for {app_name} in your browser."
        )

class OpenUrlTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="open_url",
            description="Open any web address, website, or search query in a new browser tab.",
            is_destructive=False
        )

    async def execute(self, url: str, **kwargs) -> ToolResult:
        clean = url.strip()
        clean_lower = clean.lower()

        final_url = None
        for site_name, site_url in COMMON_WEBSITES.items():
            if clean_lower == site_name or clean_lower in site_name:
                final_url = site_url
                break

        if not final_url:
            if clean.startswith("http://") or clean.startswith("https://"):
                final_url = clean
            elif re.search(r"^[a-zA-Z0-9\-]+(\.[a-zA-Z]{2,})", clean):
                final_url = f"https://{clean}"
            else:
                final_url = f"https://www.google.com/search?q={clean}"

        open_url_system(final_url)
        return ToolResult(
            tool_name=self.name,
            success=True,
            output={"type": "url", "url": final_url},
            voice_summary="Opening that in your browser."
        )

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
