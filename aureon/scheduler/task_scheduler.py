import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from aureon.config import settings
from aureon.memory.memory_manager import MemoryManager

logger = logging.getLogger("aureon.scheduler")

class TaskScheduler:
    """
    Autonomous background task runner:
    - Monitors active_tasks.json
    - Executes scheduled interval workflows
    - Records persistent events to memory_ledger.md
    """

    def __init__(self):
        self.tasks_file = settings.active_tasks_file
        self.memory = MemoryManager()
        self.is_running = False
        self._loop_task: Optional[asyncio.Task] = None

    def get_tasks(self) -> List[Dict[str, Any]]:
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("active_tasks", [])
        except Exception as e:
            logger.error(f"Failed to read tasks file: {e}")
        return []

    def save_tasks(self, tasks: List[Dict[str, Any]]):
        try:
            data = {"active_tasks": tasks, "updated_at": datetime.now().isoformat()}
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write tasks file: {e}")

    def add_task(self, title: str, interval_seconds: int = 3600, task_type: str = "health_check"):
        tasks = self.get_tasks()
        task = {
            "id": f"task_{int(datetime.now().timestamp())}",
            "title": title,
            "task_type": task_type,
            "interval_seconds": interval_seconds,
            "last_run": None,
            "created_at": datetime.now().isoformat()
        }
        tasks.append(task)
        self.save_tasks(tasks)
        self.memory.log_event("scheduler_task_added", f"{title} (every {interval_seconds}s)")
        return task

    async def _execute_task(self, task: Dict[str, Any]):
        title = task.get("title", "Unnamed task")
        task_type = task.get("task_type", "general")
        logger.info(f"Executing scheduled workflow: {title} ({task_type})")

        # Example task executions
        if task_type == "telemetry_snapshot":
            import psutil
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            self.memory.log_event("telemetry_snapshot", f"CPU: {cpu}%, RAM: {mem}%")
        else:
            self.memory.log_event("scheduled_task_executed", f"{title}")

        task["last_run"] = datetime.now().isoformat()

    async def _scheduler_loop(self):
        logger.info("Autonomous Task Scheduler started.")
        while self.is_running:
            try:
                tasks = self.get_tasks()
                now = datetime.now()
                modified = False

                for task in tasks:
                    interval = task.get("interval_seconds", 3600)
                    last_run_str = task.get("last_run")

                    should_run = False
                    if not last_run_str:
                        should_run = True
                    else:
                        last_run = datetime.fromisoformat(last_run_str)
                        if (now - last_run).total_seconds() >= interval:
                            should_run = True

                    if should_run:
                        await self._execute_task(task)
                        modified = True

                if modified:
                    self.save_tasks(tasks)

            except Exception as e:
                logger.error(f"Scheduler loop exception: {e}")

            # Cycle every 30 seconds
            await asyncio.sleep(30.0)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._loop_task = asyncio.create_task(self._scheduler_loop())

    def stop(self):
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
