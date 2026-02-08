"""FastAPI の依存解決を集約する."""

from typing import Annotated, cast

from fastapi import Depends, Request

from codex_httpd.app_container import AppContainer
from codex_httpd.usecases.events import EventsUseCase
from codex_httpd.usecases.interrupt import InterruptUseCase
from codex_httpd.usecases.threads import ThreadsUseCase
from codex_httpd.usecases.turns import TurnsUseCase


def get_container(request: Request) -> AppContainer:
    """アプリケーションコンテナを取得する."""
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise RuntimeError("アプリケーションコンテナが初期化されていません。")
    return cast(AppContainer, container)


ContainerDep = Annotated[AppContainer, Depends(get_container)]


def get_threads_use_case(container: ContainerDep) -> ThreadsUseCase:
    """Thread 系エンドポイントで利用する UseCase を返す."""
    return container.threads_use_case


def get_turns_use_case(container: ContainerDep) -> TurnsUseCase:
    """Turn 系エンドポイントで利用する UseCase を返す."""
    return container.turns_use_case


def get_events_use_case(container: ContainerDep) -> EventsUseCase:
    """Streaming 系エンドポイントで利用する UseCase を返す."""
    return container.events_use_case


def get_interrupt_use_case(container: ContainerDep) -> InterruptUseCase:
    """Interrupt 系エンドポイントで利用する UseCase を返す."""
    return container.interrupt_use_case
