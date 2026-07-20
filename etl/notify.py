"""Alerting — Telegram notifications (the Teams-callback analogue).

Airflow calls ``on_failure_callback`` / ``on_success_callback`` at the end of a
run; those build a message and send it here. If no bot token is configured the
call is a logged no-op, so the pipeline never fails just because alerting is not
set up (secrets come from the environment, never the code).
"""

from __future__ import annotations

import logging
import os

import requests

log = logging.getLogger(__name__)
API = "https://api.telegram.org/bot{token}/sendMessage"


def build_message(dag_id: str, state: str, run_id: str | None = None) -> str:
    """Compose a short, human-readable alert line."""
    emoji = {"success": "✅", "failed": "❌"}.get(state, "ℹ️")
    tail = f" · {run_id}" if run_id else ""
    return f"{emoji} {dag_id}: {state}{tail}"


def telegram_notify(message: str, timeout: int = 10) -> bool:
    """Send ``message`` to Telegram; return True if sent, False if not configured."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        log.info("telegram not configured; skipping alert: %s", message)
        return False
    response = requests.post(
        API.format(token=token),
        json={"chat_id": chat_id, "text": message},
        timeout=timeout,
    )
    response.raise_for_status()
    return True
