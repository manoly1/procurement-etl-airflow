"""Tests for the alerting layer (no network)."""

from __future__ import annotations

import etl.notify as notify
from etl.notify import build_message, telegram_notify


def test_build_message_failure() -> None:
    msg = build_message("weekly_procurement_etl", "failed", "run-1")
    assert "failed" in msg
    assert "❌" in msg
    assert "run-1" in msg


def test_build_message_success() -> None:
    assert "✅" in build_message("dag_x", "success")


def test_telegram_noop_without_config(monkeypatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    # No token -> logged no-op, never raises, so the pipeline doesn't fail.
    assert telegram_notify("hi") is False


def test_telegram_sends_when_configured(monkeypatch) -> None:
    captured = {}

    class _Resp:
        def raise_for_status(self) -> None:
            pass

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _Resp()

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TESTTOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(notify.requests, "post", fake_post)

    assert telegram_notify("hello") is True
    assert captured["json"] == {"chat_id": "12345", "text": "hello"}
    assert "TESTTOKEN" in captured["url"]
