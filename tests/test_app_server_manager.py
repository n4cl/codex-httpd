"""app-server 子プロセス管理の挙動を検証する."""

import asyncio
import sys
from pathlib import Path

from codex_httpd.infrastructure.app_server_manager import AppServerProcessManager


def test_startup_launches_process_and_shutdown_stops(tmp_path: Path) -> None:
    """起動時に子プロセスを起動し、終了時に停止することを確認する."""
    script = tmp_path / "sleep_forever.py"
    script.write_text("import time\nwhile True:\n    time.sleep(1)\n")
    manager = AppServerProcessManager(
        command=(sys.executable, str(script)),
        monitor_interval_sec=0.05,
        restart_backoff_sec=0.05,
        shutdown_timeout_sec=0.2,
    )

    async def scenario() -> None:
        await manager.startup()
        assert manager.started is True
        assert manager.process is not None
        assert manager.process.returncode is None

        await manager.shutdown()
        assert manager.started is False
        assert manager.process is None

    asyncio.run(scenario())


def test_monitor_restarts_process_after_crash(tmp_path: Path) -> None:
    """子プロセス異常終了時に監視タスクが再起動することを確認する."""
    marker = tmp_path / "marker.txt"
    script = tmp_path / "crash_then_sleep.py"
    script.write_text(
        "import pathlib\n"
        "import sys\n"
        "import time\n"
        f"marker = pathlib.Path({str(marker)!r})\n"
        "if marker.exists():\n"
        "    while True:\n"
        "        time.sleep(1)\n"
        "marker.write_text('1')\n"
        "sys.exit(17)\n"
    )
    manager = AppServerProcessManager(
        command=(sys.executable, str(script)),
        monitor_interval_sec=0.05,
        restart_backoff_sec=0.05,
        shutdown_timeout_sec=0.2,
    )

    async def scenario() -> None:
        await manager.startup()
        # 最初のクラッシュと再起動を監視ループが処理するまで待つ。
        for _ in range(40):
            if manager.restart_count >= 1 and manager.process is not None and manager.process.returncode is None:
                break
            await asyncio.sleep(0.05)

        assert manager.restart_count >= 1
        assert manager.process is not None
        assert manager.process.returncode is None

        await manager.shutdown()

    asyncio.run(scenario())
