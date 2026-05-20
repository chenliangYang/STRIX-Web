"""Command builder for STRIX CLI."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class StrixCommand:
    """STRIX command configuration."""

    binary: str
    target: str
    run_id: str
    output_dir: str
    scan_mode: str = "standard"
    interactive: bool = False
    instruction: str = None
    timeout_seconds: int = 7200

    def to_args(self) -> list[str]:
        """Build command argument list."""
        args = [self.binary]

        if not self.interactive:
            args.append("-n")

        args.extend(["--target", self.target])
        args.extend(["--scan-mode", self.scan_mode])
        args.extend(["--run-id", self.run_id])
        args.extend(["--output-dir", self.output_dir])

        if self.instruction:
            args.extend(["--instruction", self.instruction])

        return args


class CommandBuilder:
    """Builder for STRIX commands."""

    def __init__(self, binary: str = "python", script_path: str = None):
        self.binary = binary
        self.script_path = script_path or "fake_strix.py"

    def build_non_interactive(
        self,
        target: str,
        run_id: str,
        output_dir: str,
        scan_mode: str = "standard",
        instruction: str = None,
        timeout_seconds: int = 7200,
    ) -> StrixCommand:
        """Build non-interactive command."""
        strix_bin = f"{self.binary} {self.script_path}" if ".py" in self.script_path else self.binary

        return StrixCommand(
            binary=strix_bin,
            target=target,
            run_id=run_id,
            output_dir=output_dir,
            scan_mode=scan_mode,
            interactive=False,
            instruction=instruction,
            timeout_seconds=timeout_seconds,
        )

    def build_interactive(
        self,
        target: str,
        run_id: str,
        output_dir: str,
        scan_mode: str = "standard",
        instruction: str = None,
    ) -> StrixCommand:
        """Build interactive command."""
        strix_bin = f"{self.binary} {self.script_path}" if ".py" in self.script_path else self.binary

        return StrixCommand(
            binary=strix_bin,
            target=target,
            run_id=run_id,
            output_dir=output_dir,
            scan_mode=scan_mode,
            interactive=True,
            instruction=instruction,
        )

    def build_fake_non_interactive(
        self,
        target: str,
        run_id: str,
        output_dir: str,
        scan_mode: str = "standard",
        fail: bool = False,
    ) -> list[str]:
        """Build fake STRIX non-interactive command for testing."""
        script_path = Path(__file__).parent.parent.parent / "fake_strix.py"
        args = [
            "python",
            str(script_path),
            "-n",
            "--target", target,
            "--run-id", run_id,
            "--output-dir", output_dir,
            "--scan-mode", scan_mode,
        ]
        if fail:
            args.append("--fail")
        return args
