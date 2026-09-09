import pytest
import asyncio
from aureon.tools.base import registry
from aureon.tools.system_tools import GetSystemStatusTool, DeleteFileTool
from aureon.memory.memory_manager import MemoryManager
from aureon.voice.tts_engine import clean_text_for_speech
from aureon.orchestrator import Orchestrator

def test_voice_sanitizer():
    raw = "[TOOL: launch_app]\n[ARGS: {\"app_name\": \"notepad\"}]\n[CONFIRM: no]\nLaunching notepad at C:\\Windows\\notepad.exe. Check https://example.com"
    cleaned = clean_text_for_speech(raw)
    assert "[TOOL:" not in cleaned
    assert "https://" not in cleaned
    assert "the requested link" in cleaned
    assert "the file path" in cleaned

def test_memory_manager_profile():
    mm = MemoryManager()
    profile = mm.load_profile()
    assert profile.get("github_username") == "revanthbarthu"
    assert "Windows" in profile.get("os")

    summary = mm.get_context_summary()
    assert "revanthbarthu" in summary

    mm.add_learned_fact("Primary shell preference is PowerShell.")
    updated_summary = mm.get_context_summary()
    assert "PowerShell" in updated_summary

@pytest.mark.asyncio
async def test_destructive_tool_safety_gate():
    # Attempting to run delete_file without confirmation must quarantine
    res_unconfirmed = await registry.run_tool("delete_file", {"path": "non_existent_dummy.txt"}, confirmed=False)
    assert res_unconfirmed.requires_confirmation is True
    assert "quarantined" in res_unconfirmed.output.lower()

@pytest.mark.asyncio
async def test_nondestructive_tool():
    res = await registry.run_tool("get_system_status", {}, confirmed=False)
    assert res.requires_confirmation is False
    assert res.success is True
    assert "cpu_percent" in res.output

@pytest.mark.asyncio
async def test_orchestrator_tool_parsing():
    orch = Orchestrator()
    sample_text = '[TOOL: launch_app]\n[ARGS: {"app_name": "notepad"}]\n[CONFIRM: no]\nI am launching Notepad.'
    parsed = orch._parse_tool_call(sample_text)
    assert parsed is not None
    assert parsed["name"] == "launch_app"
    assert parsed["args"]["app_name"] == "notepad"
    assert parsed["declared_confirm"] is False
