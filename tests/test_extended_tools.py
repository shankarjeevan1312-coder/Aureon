import pytest
import asyncio
from pathlib import Path
from aureon.tools.base import registry
from aureon.tools.hardware_tools import GetBatteryStatusTool, GetNetworkInfoTool
from aureon.tools.media_tools import ClipboardWriteTool, ClipboardReadTool, ListActiveWindowsTool, WriteFileTool
from aureon.scheduler.task_scheduler import TaskScheduler

@pytest.mark.asyncio
async def test_battery_status_tool():
    tool = registry.get_tool("get_battery_status")
    assert tool is not None
    res = await tool.execute()
    assert res.success is True
    assert res.output is not None

@pytest.mark.asyncio
async def test_network_info_tool():
    tool = registry.get_tool("get_network_info")
    assert tool is not None
    res = await tool.execute()
    assert res.success is True
    assert "primary_ip" in res.output
    assert "hostname" in res.output

@pytest.mark.asyncio
async def test_write_and_read_file_tool(tmp_path):
    write_tool = registry.get_tool("write_file")
    read_tool = registry.get_tool("read_file")

    target = tmp_path / "test_write.txt"
    res_write = await write_tool.execute(path=str(target), content="Hello AUREON!")
    assert res_write.success is True

    res_read = await read_tool.execute(path=str(target))
    assert res_read.success is True
    assert "Hello AUREON!" in res_read.output

@pytest.mark.asyncio
async def test_clipboard_tools():
    write_tool = registry.get_tool("clipboard_write")
    read_tool = registry.get_tool("clipboard_read")

    test_str = "AUREON_TEST_TOKEN_12345"
    res_w = await write_tool.execute(text=test_str)
    assert res_w.success is True

    res_r = await read_tool.execute()
    assert res_r.success is True
    assert test_str in res_r.output

@pytest.mark.asyncio
async def test_active_windows_tool():
    tool = registry.get_tool("list_active_windows")
    assert tool is not None
    res = await tool.execute()
    assert res.success is True
    assert isinstance(res.output, list)

def test_task_scheduler_persistence():
    scheduler = TaskScheduler()
    initial_count = len(scheduler.get_tasks())
    new_task = scheduler.add_task("Hourly Diagnostics Check", interval_seconds=3600, task_type="health_check")
    assert new_task["title"] == "Hourly Diagnostics Check"

    tasks = scheduler.get_tasks()
    assert len(tasks) == initial_count + 1
    assert any(t["id"] == new_task["id"] for t in tasks)
