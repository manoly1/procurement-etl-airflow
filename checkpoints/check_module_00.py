#!/usr/bin/env python3
"""Checkpoint 0 — environment and repository skeletons.

Verifies the Stage-0 Definition of Done from the project plan:
  * Python 3.12+ available (3.11 is tolerated with a warning);
  * Git available;
  * Docker available and `docker run hello-world` works;
  * both repository skeletons are in place;
  * the guide site builds (`mkdocs build`), when mkdocs is installed.

Prints a per-line report and a final `STATUS: PASSED` / `STATUS: FAILED`.
Warnings do not fail the checkpoint; only hard failures do.

Run via:  make checkpoint 0
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

# Repo layout assumption: this file lives in
# <portfolio_repo>/checkpoints/check_module_00.py, and the learning-journey
# repo is expected as a sibling directory next to the portfolio repo.
PORTFOLIO_ROOT = Path(__file__).resolve().parent.parent
SIBLING_ROOT = PORTFOLIO_ROOT.parent
JOURNEY_ROOT = SIBLING_ROOT / "de-learning-journey"

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
    return FAIL, f"Python {version} is too old; need 3.12+ (3.11 tolerated)"


def check_git() -> tuple[str, str]:
    if not shutil.which("git"):
        return FAIL, "git not found on PATH"
    code, out = _run(["git", "--version"])
    return (OK, out) if code == 0 else (FAIL, out or "git --version failed")


def check_docker() -> tuple[str, str]:
    if not shutil.which("docker"):
        return FAIL, "docker not found on PATH (install Docker Desktop / engine)"
    code, _ = _run(["docker", "--version"])
    if code != 0:
        return FAIL, "`docker --version` failed"
    # The real test: can we actually run a container?
    code, out = _run(["docker", "run", "--rm", "hello-world"], timeout=120)
    if code == 0:
        return OK, "`docker run hello-world` succeeded"
    if "daemon" in out.lower() or "/var/run/docker.sock" in out:
        return FAIL, (
            "Docker is installed but the daemon is not running (start Docker Desktop)"
        )
    last = out.splitlines()[-1] if out else "unknown error"
    return FAIL, f"`docker run hello-world` failed: {last}"


def check_portfolio_skeleton() -> tuple[str, str]:
    required = ["Makefile", "pyproject.toml", "etl", "datagen", "checkpoints", "dags"]
    missing = [p for p in required if not (PORTFOLIO_ROOT / p).exists()]
    if missing:
        return FAIL, f"portfolio repo missing: {', '.join(missing)}"
    return OK, f"portfolio skeleton present at {PORTFOLIO_ROOT.name}/"


def check_journey_skeleton() -> tuple[str, str]:
    mkdocs_yml = JOURNEY_ROOT / "site" / "mkdocs.yml"
    if mkdocs_yml.exists():
        return OK, f"learning-journey site found at {JOURNEY_ROOT.name}/site/"
    return WARN, (
        f"learning-journey repo not found as a sibling (looked in {JOURNEY_ROOT}); "
        "clone both repos side by side to enable the site-build check"
    )


def check_site_builds() -> tuple[str, str]:
    site_dir = JOURNEY_ROOT / "site"
    if not (site_dir / "mkdocs.yml").exists():
        return WARN, "site not found next to this repo; skipped build check"
    if not shutil.which("mkdocs"):
        return WARN, (
            "mkdocs not installed; skipped (run: pip install -r site/requirements.txt)"
        )
    code, out = _run(["mkdocs", "build", "--strict", "--quiet"], timeout=180)
    if code == 0:
        return OK, "guide site builds with --strict"
    # Re-run in the site dir if the first attempt used the wrong CWD.
    try:
        proc = subprocess.run(
            ["mkdocs", "build", "--strict", "--quiet"],
            cwd=site_dir,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - report any failure verbatim
        return FAIL, f"mkdocs build error: {exc}"
    if proc.returncode == 0:
        return OK, "guide site builds with --strict"
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    return FAIL, f"mkdocs build failed: {tail[-1] if tail else 'unknown error'}"


CHECKS = [
    ("Python 3.12+", check_python),
    ("Git", check_git),
    ("Docker + hello-world", check_docker),
    ("Portfolio skeleton", check_portfolio_skeleton),
    ("Learning-journey skeleton", check_journey_skeleton),
    ("Guide site build", check_site_builds),
]


def main() -> int:
    print("Checkpoint 0 — environment & repositories")
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

    # Reminder for the one thing a script cannot check: the browser cell.
    if failed == 0:
        print("Manual step left: `mkdocs serve` in de-learning-journey/site,")
        print("open Module 0 and click Run in the live cell (needs internet).")
        print()

    ok = failed == 0
    print("STATUS: PASSED" if ok else "STATUS: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
