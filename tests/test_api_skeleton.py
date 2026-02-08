"""API スケルトン構成の挙動を検証する."""

import pytest
from fastapi.testclient import TestClient

from codex_httpd.main import app


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/threads"),
        ("get", "/threads"),
        ("get", "/threads/thread-1"),
        ("post", "/threads/thread-1/resume"),
        ("post", "/threads/thread-1/turns"),
        ("get", "/threads/thread-1/turns/turn-1/events"),
        ("post", "/threads/thread-1/turns/turn-1/interrupt"),
    ],
)
def test_api_skeleton_endpoints_return_not_implemented(method: str, path: str) -> None:
    """3.1 時点のエンドポイント雛形が 501 を返すことを確認する."""
    with TestClient(app) as client:
        response = getattr(client, method)(path)

    assert response.status_code == 501
    assert response.json()["error"]["code"] == "not_implemented"


def test_lifespan_manages_infrastructure_lifecycle() -> None:
    """アプリの lifespan が Infrastructure の起動と停止を管理することを確認する."""
    with TestClient(app) as client:
        container = client.app.state.container
        assert container.backend.started is True

    assert container.backend.started is False
