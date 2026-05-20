"""Process registry for managing running STRIX processes."""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a running process."""

    run_id: str
    task_id: str
    pid: int
    command: list[str]
    started_at: datetime
    cwd: str
    returncode: Optional[int] = None
    ended_at: Optional[datetime] = None


class ProcessRegistry:
    """Registry for managing running STRIX processes."""

    _instance: Optional["ProcessRegistry"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ProcessRegistry":
        """Singleton pattern for process registry."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the process registry."""
        if self._initialized:
            return
        self._processes: dict[str, ProcessInfo] = {}
        self._process_lock = threading.Lock()
        self._initialized = True
        logger.info("ProcessRegistry initialized")

    def register(
        self,
        run_id: str,
        task_id: str,
        pid: int,
        command: list[str],
        cwd: str,
    ) -> None:
        """Register a new running process."""
        with self._process_lock:
            process_info = ProcessInfo(
                run_id=run_id,
                task_id=task_id,
                pid=pid,
                command=command,
                started_at=datetime.utcnow(),
                cwd=cwd,
            )
            self._processes[run_id] = process_info
            logger.info(f"Registered process: run_id={run_id}, pid={pid}")

    def unregister(self, run_id: str) -> None:
        """Unregister a process after it has finished."""
        with self._process_lock:
            if run_id in self._processes:
                process_info = self._processes[run_id]
                process_info.ended_at = datetime.utcnow()
                process_info.returncode = self._get_return_code(process_info.pid)
                del self._processes[run_id]
                logger.info(f"Unregistered process: run_id={run_id}, returncode={process_info.returncode}")

    def get(self, run_id: str) -> Optional[ProcessInfo]:
        """Get process info by run_id."""
        with self._process_lock:
            return self._processes.get(run_id)

    def is_running(self, run_id: str) -> bool:
        """Check if a process is still running."""
        with self._process_lock:
            if run_id not in self._processes:
                return False
            process_info = self._processes[run_id]
            return self._is_process_alive(process_info.pid)

    def get_all_running(self) -> list[ProcessInfo]:
        """Get all running processes."""
        with self._process_lock:
            running = []
            for run_id, process_info in list(self._processes.items()):
                if self._is_process_alive(process_info.pid):
                    running.append(process_info)
                else:
                    del self._processes[run_id]
            return running

    def stop(self, run_id: str) -> bool:
        """Stop a running process by run_id."""
        with self._process_lock:
            if run_id not in self._processes:
                logger.warning(f"Process not found: run_id={run_id}")
                return False

            process_info = self._processes[run_id]

        try:
            parent = psutil.Process(process_info.pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            parent.terminate()

            gone, alive = psutil.wait_procs([parent] + children, timeout=5)
            for proc in alive:
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass

            logger.info(f"Stopped process: run_id={run_id}, pid={process_info.pid}")
            return True
        except psutil.NoSuchProcess:
            logger.warning(f"Process already terminated: run_id={run_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop process: run_id={run_id}, error={e}")
            return False

    def _is_process_alive(self, pid: int) -> bool:
        """Check if a process is alive."""
        try:
            proc = psutil.Process(pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return False

    def _get_return_code(self, pid: int) -> Optional[int]:
        """Get return code of a process."""
        try:
            proc = psutil.Process(pid)
            return proc.returncode
        except psutil.NoSuchProcess:
            return None

    def count_running(self) -> int:
        """Count of currently running processes."""
        with self._process_lock:
            return sum(1 for p in self._processes.values() if self._is_process_alive(p.pid))


def get_process_registry() -> ProcessRegistry:
    """Get the singleton process registry instance."""
    return ProcessRegistry()
