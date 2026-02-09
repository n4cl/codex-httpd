"""Codex backend の JSON-RPC 中継挙動を検証する."""

import asyncio
from pathlib import Path

from codex_httpd.infrastructure.codex_backend import CodexBackendStub


def _write_fake_codex_bin(path: Path, *, notification_method: str) -> None:
    """`codex app-server` 互換のテスト用実行ファイルを書き込む."""
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        "import sys\n"
        "if len(sys.argv) < 2 or sys.argv[1] != 'app-server':\n"
        "    sys.exit(2)\n"
        "for line in sys.stdin:\n"
        "    msg = json.loads(line)\n"
        f"    sys.stdout.write(json.dumps({{'jsonrpc': '2.0', 'method': '{notification_method}', 'params': {{'threadId': 'thread-1', 'turnId': 'turn-1'}}}}) + '\\n')\n"
        "    sys.stdout.flush()\n"
        "    response = {'jsonrpc': '2.0', 'id': msg['id'], 'result': {'ok': True}}\n"
        "    sys.stdout.write(json.dumps(response) + '\\n')\n"
        "    sys.stdout.flush()\n"
    )
    path.chmod(0o755)


def test_backend_routes_known_notification_to_turn_queue(tmp_path: Path, monkeypatch) -> None:
    """既知 notification が threadId/turnId ごとのキューへ振り分けられることを確認する."""
    fake_codex_bin = tmp_path / "fake_codex.py"
    _write_fake_codex_bin(fake_codex_bin, notification_method="turn/completed")

    monkeypatch.setenv("CODEX_HTTPD_DISABLE_APP_SERVER", "0")
    monkeypatch.setenv("CODEX_BIN", str(fake_codex_bin))

    async def scenario() -> None:
        backend = CodexBackendStub()
        await backend.startup()
        try:
            result = await backend.start_thread()
            queued = await backend.stream_turn_events(thread_id="thread-1", turn_id="turn-1")
        finally:
            await backend.shutdown()

        assert result == {"ok": True}
        assert len(queued["events"]) == 1
        assert queued["events"][0]["method"] == "turn/completed"

    asyncio.run(scenario())


def test_backend_ignores_unknown_notification(tmp_path: Path, monkeypatch, caplog) -> None:
    """未知 notification は警告ログを出して無視されることを確認する."""
    fake_codex_bin = tmp_path / "fake_codex_unknown.py"
    _write_fake_codex_bin(fake_codex_bin, notification_method="unknown/event")

    caplog.set_level("WARNING")
    monkeypatch.setenv("CODEX_HTTPD_DISABLE_APP_SERVER", "0")
    monkeypatch.setenv("CODEX_BIN", str(fake_codex_bin))

    async def scenario() -> None:
        backend = CodexBackendStub()
        await backend.startup()
        try:
            _ = await backend.start_thread()
            queued = await backend.stream_turn_events(thread_id="thread-1", turn_id="turn-1")
        finally:
            await backend.shutdown()
        return queued

    queued = asyncio.run(scenario())
    assert queued["events"] == []
    assert "unknown notification" in caplog.text
