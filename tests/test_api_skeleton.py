"""API スケルトン構成の挙動を検証する."""

import pytest
from fastapi.testclient import TestClient

from codex_httpd.main import app


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("post", "/threads", None),
        ("get", "/threads", None),
        ("get", "/threads/thread-1", None),
        ("post", "/threads/thread-1/resume", None),
        ("post", "/threads/thread-1/turns", {"input": "hello", "stream": False}),
        ("get", "/threads/thread-1/turns/turn-1/events", None),
        ("post", "/threads/thread-1/turns/turn-1/interrupt", None),
    ],
)
def test_api_skeleton_endpoints_return_not_implemented(method: str, path: str, json_body: dict[str, str | bool] | None) -> None:
    """3.1 時点のエンドポイント雛形が 501 を返すことを確認する."""
    with TestClient(app) as client:
        if json_body is None:
            response = getattr(client, method)(path)
        else:
            response = getattr(client, method)(path, json=json_body)

    assert response.status_code == 501
    assert response.json()["error"]["code"] == "not_implemented"


def test_lifespan_manages_infrastructure_lifecycle() -> None:
    """アプリの lifespan が Infrastructure の起動と停止を管理することを確認する."""
    with TestClient(app) as client:
        container = client.app.state.container
        assert container.backend.started is True

    assert container.backend.started is False
