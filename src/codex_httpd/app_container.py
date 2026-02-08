"""アプリ全体の依存オブジェクトを組み立てる."""

from codex_httpd.infrastructure.codex_backend import CodexBackendStub
from codex_httpd.usecases.events import EventsUseCase
from codex_httpd.usecases.interrupt import InterruptUseCase
from codex_httpd.usecases.threads import ThreadsUseCase
from codex_httpd.usecases.turns import TurnsUseCase


class AppContainer:
    """API 層で利用する依存オブジェクトを保持するコンテナ."""

    def __init__(self, backend: CodexBackendStub) -> None:
        """UseCase と Infrastructure を接続する."""
        self.backend = backend
        self.threads_use_case = ThreadsUseCase(backend=backend)
        self.turns_use_case = TurnsUseCase(backend=backend)
        self.events_use_case = EventsUseCase(backend=backend)
        self.interrupt_use_case = InterruptUseCase(backend=backend)

    async def startup(self) -> None:
        """Infrastructure の起動処理を実行する."""
        await self.backend.startup()

    async def shutdown(self) -> None:
        """Infrastructure の停止処理を実行する."""
        await self.backend.shutdown()


def build_container() -> AppContainer:
    """アプリ起動時に利用するコンテナを構築する."""
    backend = CodexBackendStub()
    return AppContainer(backend=backend)
