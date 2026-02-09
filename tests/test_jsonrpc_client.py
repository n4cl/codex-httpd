"""JSON-RPC 中継クライアントの挙動を検証する."""

import asyncio
import sys
from pathlib import Path

import pytest

from codex_httpd.infrastructure.app_server_manager import AppServerProcessManager
from codex_httpd.infrastructure.jsonrpc_client import JsonRpcClient
from codex_httpd.usecases.errors import RpcTimeoutError


def test_request_response_roundtrip_assigns_incremental_ids(tmp_path: Path) -> None:
    """request/response が成立し、id が連番で採番されることを確認する."""
    script = tmp_path / "fake_rpc_server.py"
    script.write_text(
        "import json\n"
        "import sys\n"
        "for line in sys.stdin:\n"
        "    msg = json.loads(line)\n"
        "    response = {\n"
        "        'jsonrpc': '2.0',\n"
        "        'id': msg['id'],\n"
        "        'result': {'echo': msg['method'], 'requestId': msg['id']},\n"
        "    }\n"
        "    sys.stdout.write(json.dumps(response) + '\\n')\n"
        "    sys.stdout.flush()\n"
    )
    manager = AppServerProcessManager(command=(sys.executable, "-u", str(script)))

    async def scenario() -> None:
        await manager.startup()
        client = JsonRpcClient(process_getter=lambda: manager.process, timeout_sec=1.0)
        await client.startup()
        try:
            first = await client.request(method="thread/start", params={})
            second = await client.request(method="thread/list", params={})
        finally:
            await client.shutdown()
            await manager.shutdown()

        assert first == {"echo": "thread/start", "requestId": 1}
        assert second == {"echo": "thread/list", "requestId": 2}

    asyncio.run(scenario())


def test_request_raises_timeout_when_response_not_returned(tmp_path: Path) -> None:
    """応答が返らない request がタイムアウトで失敗することを確認する."""
    script = tmp_path / "fake_rpc_server_no_response.py"
    script.write_text("import sys\nfor _ in sys.stdin:\n    pass\n")
    manager = AppServerProcessManager(command=(sys.executable, "-u", str(script)))

    async def scenario() -> None:
        await manager.startup()
        client = JsonRpcClient(process_getter=lambda: manager.process, timeout_sec=0.1)
        await client.startup()
        try:
            with pytest.raises(RpcTimeoutError):
                await client.request(method="thread/start", params={})
        finally:
            await client.shutdown()
            await manager.shutdown()

    asyncio.run(scenario())
