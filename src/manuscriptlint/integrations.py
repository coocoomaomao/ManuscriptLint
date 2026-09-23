from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from .models import Finding, Severity


def run_integration(tool: str, target: Path) -> list[Finding]:
    executable = shutil.which(tool)
    upper = tool.upper()

    if executable is None:
        return [
            Finding(
                target,
                Severity.WARNING,
                f"{upper}_NOT_INSTALLED",
                f"{tool} integration was requested, but the '{tool}' command is not installed.",
            )
        ]

    result = subprocess.run(
        [executable, "check", str(target)],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return [Finding(target, Severity.INFO, f"{upper}_OK",
                        f"{tool} completed without failing findings.")]

    severity = Severity.WARNING if result.returncode == 1 else Severity.ERROR
    return [
        Finding(
            target,
            severity,
            f"{upper}_FINDINGS",
            f"{tool} returned exit code {result.returncode}. "
            f"Run '{tool} check {target}' directly for the full report.",
        )
    ]
