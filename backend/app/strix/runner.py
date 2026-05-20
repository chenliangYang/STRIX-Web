"""STRIX runner for executing scans."""

import logging
import subprocess
import threading
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import TaskStatus
from app.db.session import get_db_context, get_db
from app.infra.event_bus import get_event_bus
from app.infra.lock import DistributedLock, get_lock_backend
from app.models import Task, TaskRun, RunEvent
from app.services.task_service import TaskService
from app.strix.command_builder import CommandBuilder
from app.strix.event_tailer import EventTailer
from app.strix.process_registry import get_process_registry
from app.strix.result_parser import get_result_parser

logger = logging.getLogger(__name__)

settings = get_settings()


class StrixRunner:
    """Runner for executing STRIX scans."""

    def __init__(self):
        self._command_builder = CommandBuilder(
            binary="python",
            script_path="fake_strix.py"
        )
        self._process_registry = get_process_registry()
        self._event_bus = get_event_bus()
        self._lock_backend = get_lock_backend()

    def run(self, db: Session, task_id: str, user_id: str) -> TaskRun:
        """Execute a task scan."""
        task = TaskService.get_task_by_id(db, task_id)

        # For MVP, interactive mode runs the same as non-interactive
        # Real PTY support will be added later
        is_interactive = task.interactive

        lock_key = f"task:{task_id}:running"
        lock = DistributedLock(backend=self._lock_backend, key=lock_key, timeout=3600)
        if not lock.acquire():
            raise RuntimeError("Task is already running")

        try:
            run = self._create_run(db, task, user_id)

            run_dir = Path(settings.runs_dir) / task_id / run.id
            run_dir.mkdir(parents=True, exist_ok=True)

            # Use non-interactive command for both modes in MVP
            command = self._command_builder.build_fake_non_interactive(
                target=task.target,
                run_id=run.id,
                output_dir=str(Path(settings.runs_dir) / task_id),
                scan_mode=task.scan_mode,
            )

            # Don't pipe stdout/stderr to avoid blocking
            # The process will inherit the parent's stdout/stderr
            process = subprocess.Popen(
                command,
                cwd=str(Path(__file__).parent.parent.parent),
            )

            # Check if process started successfully
            if process.poll() is not None:
                logger.error(f"Process failed to start with return code {process.returncode}")
                raise RuntimeError(f"Failed to start STRIX process")

            logger.info(f"STRIX process started with PID {process.pid}")

            self._process_registry.register(
                run_id=run.id,
                task_id=task_id,
                pid=process.pid,
                command=command,
                cwd=str(run_dir),
            )

            db.query(TaskRun).filter(TaskRun.id == run.id).update({
                "pid": process.pid,
                "status": "running",
                "started_at": datetime.utcnow(),
                "run_dir": str(run_dir),
                "strix_run_dir": str(run_dir),  # strix_run_dir is the same as run_dir
            })
            db.query(Task).filter(Task.id == task_id).update({
                "status": TaskStatus.RUNNING.value,
                "updated_at": datetime.utcnow(),
            })
            db.commit()

            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_in_executor(None, self._monitor_run_sync, run.id, task_id)

            return run

        except Exception as e:
            lock.release()
            logger.error(f"Failed to start task {task_id}: {e}")
            raise

    def _monitor_run_sync(self, run_id: str, task_id: str) -> None:
        """Monitor run synchronously in background thread."""
        logger.info(f"Starting monitor for run {run_id}")
        
        # strix_run_dir is now directly under runs_dir/<task_id>/<run_id>
        strix_run_dir = Path(settings.runs_dir) / task_id / run_id
        events_file = strix_run_dir / "events.jsonl"

        for _ in range(60):
            if events_file.exists():
                break
            time.sleep(0.5)

        if not events_file.exists():
            logger.error(f"events.jsonl not found for run {run_id}")
            self._finalize_run(run_id, task_id, exit_code=1)
            return

        tailer = EventTailer(events_file)
        tailer.open()

        try:
            last_seq = 0
            while True:
                time.sleep(0.5)
                events = list(tailer.tail())

                if events:
                    for event in events:
                        self._save_and_publish_event(run_id, event, last_seq)
                        last_seq = event.get("_seq", last_seq)

                if not self._process_registry.is_running(run_id):
                    remaining = list(tailer.tail())
                    for event in remaining:
                        self._save_and_publish_event(run_id, event, last_seq)
                        last_seq = event.get("_seq", last_seq)
                    break

        finally:
            tailer.close()
            self._finalize_run(run_id, task_id, exit_code=0)

    def _save_and_publish_event(self, run_id: str, event: dict, last_seq: int) -> None:
        """Save event to database and publish."""
        try:
            db_gen = get_db()
            db = next(db_gen)
            
            run_event = RunEvent(
                id=str(uuid.uuid4()),
                run_id=run_id,
                seq=event.get("_seq", last_seq + 1),
                event_type=event.get("type", "unknown"),
                event_time=datetime.utcfromtimestamp(time.time()),
                payload_json=event.get("data", {}),
                created_at=datetime.utcnow(),
            )
            db.add(run_event)
            db.commit()

            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self._event_bus.publish_event(run_id, event)
            )
        except Exception as e:
            logger.error(f"Failed to save event: {e}")

    def _finalize_run(self, run_id: str, task_id: str, exit_code: int) -> None:
        """Finalize run after completion."""
        try:
            db_gen = get_db()
            db = next(db_gen)

            run = db.query(TaskRun).filter(TaskRun.id == run_id).first()
            if not run:
                return

            run.exit_code = exit_code
            run.ended_at = datetime.utcnow()
            run.updated_at = datetime.utcnow()

            task = db.query(Task).filter(Task.id == task_id).first()
            strix_run_dir = Path(run.strix_run_dir) if run.strix_run_dir else None

            # Create Result record with all required fields
            from app.models import Result, Vulnerability
            result = Result(
                id=str(uuid.uuid4()),
                task_id=task_id,
                run_id=run_id,
                target=task.target if task else "",
                scan_mode=task.scan_mode if task else "standard",
                interactive=task.interactive if task else False,
                status="completed" if exit_code == 0 else "failed",
                vulnerability_count=0,
                risk_level="unknown",
                started_at=run.started_at,
                ended_at=run.ended_at,
            )
            db.add(result)

            vuln_count = 0
            if strix_run_dir and strix_run_dir.exists():
                try:
                    parser = get_result_parser(strix_run_dir)
                    parsed = parser.parse(run_id, task_id)

                    for idx, vuln_data in enumerate(parsed.vulnerabilities):
                        vuln = Vulnerability(
                            id=str(uuid.uuid4()),
                            result_id=result.id,
                            vuln_id=vuln_data.vuln_id,
                            ordinal=idx + 1,
                            title=vuln_data.title,
                            severity=vuln_data.severity,
                            vuln_type=vuln_data.vuln_type,
                            affected_target=vuln_data.affected_target,
                            verified=vuln_data.verified,
                            summary=vuln_data.summary,
                            raw_json=vuln_data.raw,
                        )
                        db.add(vuln)
                        vuln_count += 1

                    # Update result with vulnerability count and risk level
                    result.vulnerability_count = vuln_count
                    result.risk_level = parsed.risk_level

                    task = db.query(Task).filter(Task.id == task_id).first()
                    if task:
                        task.risk_level = parsed.risk_level

                except Exception as e:
                    logger.error(f"Failed to parse results: {e}")

            final_status = "completed" if exit_code == 0 else "failed"
            run.status = final_status
            result.status = final_status

            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = final_status
                task.updated_at = datetime.utcnow()

            db.commit()

            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self._event_bus.publish_status_change(
                    run_id=run_id,
                    task_id=task_id,
                    status=final_status,
                    extra={"exit_code": exit_code, "vuln_count": vuln_count},
                )
            )

            logger.info(f"Run {run_id} finalized with status {final_status}, {vuln_count} vulnerabilities")

        except Exception as e:
            logger.error(f"Failed to finalize run: {e}")
        finally:
            self._process_registry.unregister(run_id)
            lock_key = f"task:{task_id}:running"
            lock = DistributedLock(backend=self._lock_backend, key=lock_key)
            lock.release()

    def _create_run(self, db: Session, task: Task, user_id: str) -> TaskRun:
        """Create a new task run record."""
        last_run = db.query(TaskRun).filter(
            TaskRun.task_id == task.id
        ).order_by(TaskRun.run_no.desc()).first()

        run_no = (last_run.run_no + 1) if last_run else 1

        # Create run directory upfront
        run_id = str(uuid.uuid4())
        run_dir = Path(settings.runs_dir) / task.id / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        run = TaskRun(
            id=run_id,
            task_id=task.id,
            run_no=run_no,
            scan_mode=task.scan_mode,
            interactive=task.interactive,
            status="queued",
            run_dir=str(run_dir),
            strix_run_dir=str(run_dir),  # strix_run_dir is the same as run_dir
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def stop(self, db: Session, run_id: str, user_id: str) -> bool:
        """Stop a running task."""
        run = db.query(TaskRun).filter(TaskRun.id == run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")

        task_id = run.task_id

        if not self._process_registry.is_running(run_id):
            logger.warning(f"Run {run_id} is not running")
            return False

        success = self._process_registry.stop(run_id)

        if success:
            db.query(TaskRun).filter(TaskRun.id == run_id).update({
                "status": "stopped",
                "ended_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            db.query(Task).filter(Task.id == task_id).update({
                "status": TaskStatus.STOPPED.value,
                "updated_at": datetime.utcnow(),
            })
            db.commit()

            lock_key = f"task:{task_id}:running"
            lock = DistributedLock(backend=self._lock_backend, key=lock_key)
            lock.release()

            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self._event_bus.publish_status_change(
                    run_id=run_id,
                    task_id=task_id,
                    status="stopped",
                )
            )

        return success


_strix_runner: Optional[StrixRunner] = None


def get_strix_runner() -> StrixRunner:
    """Get the singleton StrixRunner instance."""
    global _strix_runner
    if _strix_runner is None:
        _strix_runner = StrixRunner()
    return _strix_runner
