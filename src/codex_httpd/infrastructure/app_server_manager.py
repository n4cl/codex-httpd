"""codex app-server 子プロセスの起動・監視・停止を管理する."""

import asyncio
import logging
import os
import signal
from asyncio.subprocess import PIPE, Process
from collections.abc import Sequence

logger = logging.getLogger("codex_httpd.app_server")


class AppServerProcessManager:
    """app-server 子プロセスのライフサイクルを管理する."""

    def __init__(
        self,
        *,
        command: Sequence[str],
        monitor_interval_sec: float = 1.0,
        restart_backoff_sec: float = 1.0,
        shutdown_timeout_sec: float = 5.0,
    ) -> None:
        """監視設定と起動コマンドを初期化する."""
        if not command:
            raise ValueError("起動コマンドは1要素以上必要です。")
        self._command = tuple(command)
        self._monitor_interval_sec = monitor_interval_sec
        self._restart_backoff_sec = restart_backoff_sec
        self._shutdown_timeout_sec = shutdown_timeout_sec

        self._process: Process | None = None
        self._monitor_task: asyncio.Task[None] | None = None
        self._stopping = False
        self._restart_count = 0

    @property
    def process(self) -> Process | None:
        """現在の子プロセスを返す."""
        return self._process

    @property
    def started(self) -> bool:
        """管理対象が起動済みかを返す."""
        return self._monitor_task is not None and not self._monitor_task.done()

    @property
    def restart_count(self) -> int:
        """異常終了後の再起動回数を返す."""
        return self._restart_count

    async def startup(self) -> None:
        """子プロセスを即時起動し、監視タスクを開始する."""
        if self.started:
            return
        self._stopping = False
        await self._spawn_process()
        self._monitor_task = asyncio.create_task(self._monitor_loop(), name="codex-app-server-monitor")

    async def shutdown(self) -> None:
        """監視タスクを停止し、子プロセスを明示的に終了する."""
        self._stopping = True
        monitor_task = self._monitor_task
        await self._stop_process()
        if monitor_task is not None:
            await monitor_task
        self._monitor_task = None
        self._process = None

    async def _spawn_process(self) -> None:
        """app-server 子プロセスを起動する."""
        self._process = await asyncio.create_subprocess_exec(
            *self._command,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            start_new_session=True,
        )
        logger.info("app-server started pid=%s command=%s", self._process.pid, " ".join(self._command))

    async def _stop_process(self) -> None:
        """app-server 子プロセスを停止する."""
        process = self._process
        if process is None:
            return
        if process.returncode is not None:
            return

        if process.pid is None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            await asyncio.wait_for(process.wait(), timeout=self._shutdown_timeout_sec)
        except TimeoutError:
            logger.warning("app-server terminate timeout. force kill pid=%s", process.pid)
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await process.wait()
        logger.info("app-server stopped pid=%s returncode=%s", process.pid, process.returncode)

    async def _monitor_loop(self) -> None:
        """子プロセスの異常終了を監視し、必要に応じて再起動する."""
        while not self._stopping:
            process = self._process
            if process is None:
                await asyncio.sleep(self._monitor_interval_sec)
                continue

            returncode = process.returncode
            if returncode is None:
                returncode = await process.wait()
            if self._stopping:
                break

            logger.warning("app-server exited unexpectedly returncode=%s. restarting...", returncode)
            self._restart_count += 1
            await asyncio.sleep(self._restart_backoff_sec)
            if self._stopping:
                break
            await self._spawn_process()
