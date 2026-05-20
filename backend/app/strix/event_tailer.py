"""Event tailer for reading events from events.jsonl files."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

logger = logging.getLogger(__name__)


class EventTailer:
    """Tailer for reading new events from events.jsonl files.

    Handles:
    - Detecting incomplete (partial) JSON lines
    - Tracking file offset for resume
    - Generating sequential event numbers
    """

    def __init__(self, events_file: Path, start_offset: int = 0):
        """Initialize the event tailer.

        Args:
            events_file: Path to the events.jsonl file
            start_offset: Byte offset to start reading from
        """
        self.events_file = Path(events_file)
        self.offset = start_offset
        self._buffer = ""
        self._seq = 0
        self._file_handle = None

    def open(self) -> None:
        """Open the events file for reading."""
        if not self.events_file.exists():
            logger.warning(f"Events file does not exist: {self.events_file}")
            return

        self._file_handle = open(self.events_file, "r", encoding="utf-8")
        if self.offset > 0:
            self._file_handle.seek(self.offset)

    def close(self) -> None:
        """Close the events file."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

    def tail(self) -> Generator[dict, None, None]:
        """Tail new events from the file.

        Yields:
            dict: Event data with seq number added
        """
        if not self._file_handle:
            self.open()

        for line in self._file_handle:
            self.offset += len(line.encode("utf-8"))
            line = line.strip()

            if not line:
                continue

            try:
                event = json.loads(line)
                self._seq += 1
                event["_seq"] = self._seq
                event["_offset"] = self.offset
                event["_timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield event
            except json.JSONDecodeError:
                self._buffer += line
                try:
                    event = json.loads(self._buffer)
                    self._buffer = ""
                    self._seq += 1
                    event["_seq"] = self._seq
                    event["_offset"] = self.offset
                    event["_timestamp"] = datetime.utcnow().isoformat() + "Z"
                    yield event
                except json.JSONDecodeError:
                    logger.debug(f"Incomplete JSON in buffer: {self._buffer[:100]}")
                    self._buffer += "\n"

    def read_all(self) -> list[dict]:
        """Read all events from the file (non-tail mode).

        Returns:
            list[dict]: All events in the file
        """
        events = []
        if not self.events_file.exists():
            return events

        with open(self.events_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                    self._seq += 1
                    event["_seq"] = self._seq
                    event["_offset"] = 0
                    event["_timestamp"] = datetime.utcnow().isoformat() + "Z"
                    events.append(event)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line: {line[:100]}")

        return events

    @property
    def current_offset(self) -> int:
        """Get current file offset."""
        return self.offset

    @property
    def current_seq(self) -> int:
        """Get current sequence number."""
        return self._seq

    def get_events_file_path(strix_run_dir: Path) -> Path:
        """Get the path to events.jsonl in a STRIX run directory.

        Args:
            strix_run_dir: Path to the STRIX run directory

        Returns:
            Path: Path to events.jsonl file
        """
        return strix_run_dir / "events.jsonl"

    def wait_for_events_file(self, timeout: float = 10.0) -> bool:
        """Wait for events.jsonl to be created.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if file was found, False if timeout
        """
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.events_file.exists():
                return True
            time.sleep(0.1)
        return False
