#!/usr/bin/env python3
"""Checkpoint 13 — CI/CD.

Validates the GitHub Actions workflow offline: it parses as YAML, triggers on
push + pull_request, and runs the full gate — ruff lint, ruff format check,
pytest, DAG compilation and dbt parse. That is the same set of checks the
`make checkpoint` line has verified stage by stage, now enforced on every PR.

Run via:  make checkpoint 13
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / ".github" / "workflows" / "ci.yml"

# Command fragments every gate step must contain, by intent.
REQUIRED_STEPS = {
    "ruff check": "ruff check",
    "ruff format": "ruff format --check",
    "pytest": "pytest",
    "dag compile": "py_compile dags",
    "dbt parse": "dbt parse",
}


def main() -> int:
    print("Checkpoint 13 — CI/CD")
    print("-" * 44)

    if not WORKFLOW.exists():
        print(f"  ✖ missing {WORKFLOW.relative_to(REPO)}")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1

    import yaml

    try:
        wf = yaml.safe_load(WORKFLOW.read_text())
    except yaml.YAMLError as e:
        print(f"  ✖ workflow YAML does not parse — {e}")
        print("-" * 44)
        print("STATUS: FAILED")
        return 1
    print(f"  ✔ workflow parses ({WORKFLOW.relative_to(REPO)})")

    # YAML parses the bare key `on:` as boolean True — accept either spelling.
    triggers = wf.get("on", wf.get(True, {}))
    trig_ok = isinstance(triggers, dict) and {"push", "pull_request"} <= set(triggers)
    print(f"  {'✔' if trig_ok else '✖'} triggers on push + pull_request")

    # Flatten every run: script across all jobs/steps.
    scripts = "\n".join(
        step.get("run", "")
        for job in wf.get("jobs", {}).values()
        for step in job.get("steps", [])
    )

    steps_ok = True
    for label, fragment in REQUIRED_STEPS.items():
        present = fragment in scripts
        steps_ok = steps_ok and present
        print(f"  {'✔' if present else '✖'} gate step: {label}")

    ok = trig_ok and steps_ok
    print("-" * 44)
    print("STATUS: PASSED" if ok else "STATUS: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
