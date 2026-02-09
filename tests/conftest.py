"""テスト全体の共通設定."""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def disable_app_server_for_tests() -> None:
    """テスト中は app-server 子プロセス起動を無効化する."""
    previous = os.environ.get("CODEX_HTTPD_DISABLE_APP_SERVER")
    os.environ["CODEX_HTTPD_DISABLE_APP_SERVER"] = "1"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("CODEX_HTTPD_DISABLE_APP_SERVER", None)
        else:
            os.environ["CODEX_HTTPD_DISABLE_APP_SERVER"] = previous
