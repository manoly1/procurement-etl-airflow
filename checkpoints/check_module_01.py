#!/usr/bin/env python3
"""Checkpoint 1 — the developer toolbelt.

Verifies the Stage-0 / Module-1 Definition of Done: the tools are installed
and a project is properly isolated. On Windows this is expected to run inside
WSL2; on macOS/Linux it runs natively.

Checks:
  * Python 3.12+;
  * Git available AND identity configured (user.name / user.email);
  * uv installed;
  * Docker works (`docker run hello-world`);
  * a virtual environment is active (not the system Python);
  * running under Linux/WSL rather than bare Windows (warning only).

Prints a per-line report and a final `STATUS: PASSED` / `STATUS: FAILED`.
Warnings do not fail the checkpoint; only hard failures do.

Run via:  make checkpoint 1
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys

OK, WARN, FAIL = "ok", "warn", "fail"
GLYPH = {OK: "✔", WARN: "!", FAIL: "✖"}  # ✔ ! ✖


def _run(cmd: list[str], timeout: int = 120) -> tuple[int, str]:
    """Run a command, returning (returncode, combined_output)."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return proc.returncode, (proc.stdout + proc.stderr).strip()
    except FileNotFoundError:
        return 127, f"{cmd[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, f"{cmd[0]}: timed out after {timeout}s"


def check_python() -> tuple[str, str]:
    major, minor = sys.version_info[:2]
    version = f"{major}.{minor}.{sys.version_info[2]}"
    if (major, minor) >= (3, 12):
        return OK, f"Python {version}"
    if (major, minor) == (3, 11):
        return WARN, f"Python {version} works, but the plan targets 3.12+"
    return FAIL, f"Python {version} is too old; need 3.12+"


def check_git_identity() -> tuple[str, str]:
    if not shutil.which("git"):
        return FAIL, "git not found on PATH"
    name = _run(["git", "config", "--get", "user.name"])[1]
    email = _run(["git", "config", "--get", "user.email"])[1]
    if not name or not email:
        return FAIL, "git identity not set (git config --global user.name / user.email)"
    return OK, f"git configured as {name} <{email}>"


def check_uv() -> tuple[str, str]:
    if not shutil.which("uv"):
        return FAIL, "uv not found (curl -LsSf https://astral.sh/uv/install.sh | sh)"
    code, out = _run(["uv", "--version"])
    return (OK, out) if code == 0 else (FAIL, out or "uv --version failed")


def check_docker() -> tuple[str, str]:
    if not shutil.which("docker"):
        return FAIL, "docker not found (install Docker Desktop; enable WSL integration)"
    code, _ = _run(["docker", "--version"])
    if code != 0:
        return FAIL, "`docker --version` failed"
    code, out = _run(["docker", "run", "--rm", "hello-world"], timeout=120)
    if code == 0:
        return OK, "`docker run hello-world` succeeded"
    if "daemon" in out.lower() or "docker.sock" in out:
        return FAIL, "Docker installed but daemon not reachable (start Docker Desktop)"
    return FAIL, "`docker run hello-world` failed"


def check_venv() -> tuple[str, str]:
    # A venv makes sys.prefix diverge from the base interpreter prefix.
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv or os.environ.get("VIRTUAL_ENV"):
        return OK, f"virtual environment active ({sys.prefix})"
    return FAIL, "no virtual environment active (create with `uv venv` and activate it)"


def check_platform() -> tuple[str, str]:
    if os.name == "nt":
        return WARN, "running on native Windows; the plan expects WSL2 (Ubuntu)"
    release = platform.uname().release.lower()
    if "microsoft" in release or "wsl" in release:
        return OK, "running under WSL2"
    return OK, f"running under {platform.system()}"


CHECKS = [
    ("Python 3.12+", check_python),
    ("Git + identity", check_git_identity),
    ("uv", check_uv),
    ("Docker + hello-world", check_docker),
    ("Virtual environment", check_venv),
    ("Platform (WSL/Linux)", check_platform),
]


def main() -> int:
    print("Checkpoint 1 — developer toolbelt")
    print("-" * 44)
    statuses: list[str] = []
    for label, fn in CHECKS:
        try:
            status, detail = fn()
        except Exception as exc:  # noqa: BLE001 - a crashing check is a failure
            status, detail = FAIL, f"check crashed: {exc}"
        statuses.append(status)
        print(f"  {GLYPH[status]} {label}: {detail}")

    print("-" * 44)
    failed = statuses.count(FAIL)
    warned = statuses.count(WARN)
    passed = statuses.count(OK)
    print(f"{passed} passed, {warned} warning(s), {failed} failed")
    print()

    ok = failed == 0
    print("STATUS: PASSED" if ok else "STATUS: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
