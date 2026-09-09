import socket
import psutil
import asyncio
from typing import Optional, Dict, Any
from aureon.tools.base import BaseTool, ToolResult, registry

class GetBatteryStatusTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="get_battery_status",
            description="Inspect system battery percentage, charging state, and remaining operating time.",
            is_destructive=False
        )

    async def execute(self, **kwargs) -> ToolResult:
        battery = psutil.sensors_battery()
        if battery is None:
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={"status": "Desktop PC / AC Power connected (no battery detected)"},
                voice_summary="System is running on continuous direct AC power."
            )

        percent = battery.percent
        plugged = battery.power_plugged
        seconds_left = battery.secsleft

        hours = round(seconds_left / 3600, 1) if seconds_left > 0 else "calculating"
        state = "plugged in and charging" if plugged else "discharging on battery"

        data = {
            "percent": percent,
            "power_plugged": plugged,
            "estimated_hours_remaining": hours
        }

        voice = f"Battery is at {percent} percent, currently {state}."
        if not plugged and seconds_left > 0:
            voice += f" Approximately {hours} hours remaining."

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=data,
            voice_summary=voice
        )

class GetNetworkInfoTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="get_network_info",
            description="Inspect local IP address, active network adapters, and network traffic telemetry.",
            is_destructive=False
        )

    async def execute(self, **kwargs) -> ToolResult:
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"

        net_io = psutil.net_io_counters()
        data = {
            "hostname": hostname,
            "primary_ip": local_ip,
            "bytes_sent_mb": round(net_io.bytes_sent / (1024 ** 2), 2),
            "bytes_recv_mb": round(net_io.bytes_recv / (1024 ** 2), 2)
        }

        voice = f"Connected on local IP {local_ip}. Total data received: {data['bytes_recv_mb']} megabytes."
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=data,
            voice_summary=voice
        )

class VolumeControlTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="volume_control",
            description="Adjust or inspect Windows master volume (e.g. level 0-100 or mute/unmute).",
            is_destructive=False
        )

    async def execute(self, action: str = "get", level: Optional[int] = None, **kwargs) -> ToolResult:
        # PowerShell script using Windows Audio API / SendKeys fallback
        if action == "mute":
            ps_cmd = "$wscript = New-Object -ComObject WScript.Shell; $wscript.SendKeys([char]173)"
            voice = "Audio muted."
        elif action == "unmute":
            ps_cmd = "$wscript = New-Object -ComObject WScript.Shell; $wscript.SendKeys([char]173)"
            voice = "Audio unmuted."
        elif action == "set" and level is not None:
            # Clamp level 0 to 100
            level = max(0, min(100, int(level)))
            # Approximate volume adjustment via PowerShell Sound Volume steps
            ps_cmd = f"$wscript = New-Object -ComObject WScript.Shell; 1..50 | ForEach-Object {{ $wscript.SendKeys([char]174) }}; 1..{level // 2} | ForEach-Object {{ $wscript.SendKeys([char]175) }}"
            voice = f"Volume adjusted to approximately {level} percent."
        else:
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={"status": "Volume controller ready."},
                voice_summary="Volume controller operational."
            )

        try:
            proc = await asyncio.create_subprocess_shell(
                f"powershell.exe -NoProfile -Command \"{ps_cmd}\"",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Volume action '{action}' executed successfully.",
                voice_summary=voice
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=str(e),
                voice_summary="Failed to adjust volume."
            )

registry.register(GetBatteryStatusTool())
registry.register(GetNetworkInfoTool())
registry.register(VolumeControlTool())
