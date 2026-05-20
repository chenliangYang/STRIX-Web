"""Result parser for parsing STRIX scan results."""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class ParsedVulnerability:
    """Represents a parsed vulnerability."""

    def __init__(
        self,
        vuln_id: str,
        title: str,
        severity: str,
        vuln_type: str = None,
        affected_target: str = None,
        verified: bool = False,
        summary: str = None,
        markdown_path: str = None,
        raw: dict = None,
    ):
        self.vuln_id = vuln_id
        self.title = title
        self.severity = severity
        self.vuln_type = vuln_type
        self.affected_target = affected_target
        self.verified = verified
        self.summary = summary
        self.markdown_path = markdown_path
        self.raw = raw or {}


class ParsedResult:
    """Represents a parsed scan result."""

    def __init__(
        self,
        run_id: str,
        task_id: str,
        vulnerabilities: list[ParsedVulnerability] = None,
        summary: dict = None,
        artifacts: list[str] = None,
    ):
        self.run_id = run_id
        self.task_id = task_id
        self.vulnerabilities = vulnerabilities or []
        self.summary = summary or {}
        self.artifacts = artifacts or []

    @property
    def risk_level(self) -> str:
        """Calculate risk level based on vulnerabilities."""
        severities = [v.severity for v in self.vulnerabilities]
        if "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        elif "low" in severities:
            return "low"
        elif len(self.vulnerabilities) == 0:
            return "none"
        return "unknown"


class ResultParser:
    """Parser for STRIX scan results."""

    SEVERITY_MAP = {
        "critical": "high",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "low",
        "informational": "low",
    }

    def __init__(self, strix_run_dir: Path):
        """Initialize the result parser.

        Args:
            strix_run_dir: Path to the STRIX run directory
        """
        self.strix_run_dir = Path(strix_run_dir)
        self.artifacts_dir = self.strix_run_dir / "artifacts"
        self.events_file = self.strix_run_dir / "events.jsonl"

    def parse(self, run_id: str, task_id: str) -> ParsedResult:
        """Parse scan results from STRIX run directory.

        Args:
            run_id: Run ID
            task_id: Task ID

        Returns:
            ParsedResult with parsed vulnerabilities and summary
        """
        vulnerabilities = []
        summary = {"total": 0, "high": 0, "medium": 0, "low": 0}
        artifacts = []

        # First, try to parse from markdown files
        if self.artifacts_dir.exists():
            for artifact_file in self.artifacts_dir.glob("*.md"):
                artifacts.append(str(artifact_file.relative_to(self.strix_run_dir)))
                vuln = self._parse_vulnerability_markdown(artifact_file, run_id)
                if vuln:
                    vulnerabilities.append(vuln)

        # If no markdown files, try to parse from events.jsonl
        if not vulnerabilities and self.events_file.exists():
            try:
                events = self._read_events_file()
                for event in events:
                    if event.get("type") == "vulnerability_found":
                        data = event.get("data", {})
                        vuln = ParsedVulnerability(
                            vuln_id=data.get("vuln_id", f"vuln-{len(vulnerabilities) + 1}"),
                            title=data.get("title", "Unknown"),
                            severity=self.SEVERITY_MAP.get(data.get("severity", "unknown"), data.get("severity", "unknown")),
                            vuln_type=data.get("type"),
                            affected_target=data.get("url"),
                            verified=True,
                            summary=self._generate_summary_from_event(data),
                            raw=data,
                        )
                        vulnerabilities.append(vuln)
                    elif event.get("type") == "scan_complete":
                        summary_data = event.get("data", {}).get("summary")
                        if summary_data:
                            summary["total"] = summary_data.get("total_vulnerabilities", len(vulnerabilities))
                            summary["high"] = summary_data.get("high", 0)
                            summary["medium"] = summary_data.get("medium", 0)
                            summary["low"] = summary_data.get("low", 0)
            except Exception as e:
                logger.warning(f"Failed to parse events file: {e}")

        # Count vulnerabilities by severity
        for vuln in vulnerabilities:
            severity = self.SEVERITY_MAP.get(vuln.severity, vuln.severity)
            if severity == "high":
                summary["high"] += 1
            elif severity == "medium":
                summary["medium"] += 1
            else:
                summary["low"] += 1
            summary["total"] += 1

        return ParsedResult(
            run_id=run_id,
            task_id=task_id,
            vulnerabilities=vulnerabilities,
            summary=summary,
            artifacts=artifacts,
        )

    def _read_events_file(self) -> list[dict]:
        """Read events from events.jsonl file."""
        events = []
        if self.events_file.exists():
            with open(self.events_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        return events

    def _generate_summary_from_event(self, data: dict) -> str:
        """Generate summary from vulnerability event data."""
        title = data.get("title", "")
        severity = data.get("severity", "")
        url = data.get("url", "")
        return f"{title} ({severity}) at {url}"

    def _parse_vulnerability_markdown(self, md_file: Path, run_id: str) -> Optional[ParsedVulnerability]:
        """Parse a vulnerability markdown file.

        Args:
            md_file: Path to the markdown file
            run_id: Run ID for artifact path

        Returns:
            ParsedVulnerability or None if parsing failed
        """
        try:
            content = md_file.read_text(encoding="utf-8")

            title = self._extract_title(content)
            severity = self._extract_severity(content)
            vuln_type = self._extract_vuln_type(content, title)
            affected_target = self._extract_url(content)

            return ParsedVulnerability(
                vuln_id=md_file.stem,
                title=title,
                severity=severity,
                vuln_type=vuln_type,
                affected_target=affected_target,
                verified=True,
                summary=self._extract_summary(content),
                markdown_path=str(md_file.relative_to(self.strix_run_dir)),
                raw={
                    "file": str(md_file),
                    "content_preview": content[:500],
                },
            )
        except Exception as e:
            logger.warning(f"Failed to parse vulnerability markdown {md_file}: {e}")
            return None

    def _extract_title(self, content: str) -> str:
        """Extract vulnerability title from markdown."""
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return "Unknown Vulnerability"

    def _extract_severity(self, content: str) -> str:
        """Extract severity from markdown."""
        content_lower = content.lower()

        severity_patterns = [
            r"severity:\s*(critical|high|medium|low|info)",
            r"severity\s*\|\s*(critical|high|medium|low|info)",
            r"\*\*severity:\*\*\s*(critical|high|medium|low|info)",
        ]

        for pattern in severity_patterns:
            match = re.search(pattern, content_lower)
            if match:
                return self.SEVERITY_MAP.get(match.group(1), match.group(1))

        return "unknown"

    def _extract_vuln_type(self, content: str, title: str) -> str:
        """Extract vulnerability type from title."""
        title_lower = title.lower()

        vuln_types = [
            "sql injection", "xss", "cross-site scripting",
            "csrf", "csrf", "ssrf", "lfi", "rfi",
            "xxe", "command injection", "path traversal",
            "idor", "broken authentication", "sensitive data exposure",
        ]

        for vuln_type in vuln_types:
            if vuln_type in title_lower:
                return vuln_type.upper() if len(vuln_type) <= 4 else vuln_type.title()

        return "Unknown"

    def _extract_url(self, content: str) -> Optional[str]:
        """Extract target URL from markdown."""
        url_pattern = r"https?://[^\s\)>\"']+"
        match = re.search(url_pattern, content)
        return match.group(0) if match else None

    def _extract_summary(self, content: str) -> str:
        """Extract summary from markdown."""
        lines = content.split("\n")
        summary_lines = []
        in_summary = False

        for line in lines:
            line = line.strip()

            if line.lower().startswith("## summary"):
                in_summary = True
                continue

            if line.startswith("## "):
                in_summary = False

            if in_summary and line and not line.startswith("-"):
                summary_lines.append(line)

            if in_summary and len(summary_lines) >= 3:
                break

        return " ".join(summary_lines)[:500] if summary_lines else ""

    def parse_from_events(self, events: list[dict], run_id: str, task_id: str) -> ParsedResult:
        """Parse results directly from events (alternative method).

        Args:
            events: List of events from events.jsonl
            run_id: Run ID
            task_id: Task ID

        Returns:
            ParsedResult with vulnerabilities from events
        """
        vulnerabilities = []
        summary = {"total": 0, "high": 0, "medium": 0, "low": 0}

        for event in events:
            if event.get("type") == "vulnerability_found":
                data = event.get("data", {})
                vuln = ParsedVulnerability(
                    vuln_id=data.get("vuln_id", f"vuln-{len(vulnerabilities) + 1}"),
                    title=data.get("title", "Unknown"),
                    severity=self.SEVERITY_MAP.get(data.get("severity", "unknown"), data.get("severity", "unknown")),
                    vuln_type=data.get("type"),
                    affected_target=data.get("url"),
                    verified=True,
                    raw=data,
                )
                vulnerabilities.append(vuln)

            elif event.get("type") == "scan_complete":
                summary = event.get("data", {}).get("summary", summary)

        for vuln in vulnerabilities:
            severity = vuln.severity
            if severity == "high":
                summary["high"] = summary.get("high", 0) + 1
            elif severity == "medium":
                summary["medium"] = summary.get("medium", 0) + 1
            else:
                summary["low"] = summary.get("low", 0) + 1

        return ParsedResult(
            run_id=run_id,
            task_id=task_id,
            vulnerabilities=vulnerabilities,
            summary=summary,
        )


def get_result_parser(strix_run_dir: Path) -> ResultParser:
    """Create a result parser for a STRIX run directory."""
    return ResultParser(strix_run_dir)
