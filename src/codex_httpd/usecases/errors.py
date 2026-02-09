"""UseCase 層の共通例外."""

from typing import Any


class ApplicationError(Exception):
    """API に返却可能なアプリケーション例外."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        """例外の公開メッセージと補足情報を保持する."""
        super().__init__(message)
        self.message = message
        self.details = details

    def to_response(self) -> dict[str, Any]:
        """HTTP エラー応答へ変換する."""
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details is not None:
            payload["details"] = self.details
        return {"error": payload}


class FeatureNotImplementedError(ApplicationError):
    """未実装機能に対する例外."""

    status_code = 501
    code = "not_implemented"

    def __init__(self, operation: str) -> None:
        """未実装の操作名を補足情報に保持する."""
        super().__init__(
            message="この操作は未実装です。",
            details={"operation": operation},
        )


class BackendUnavailableError(ApplicationError):
    """Codex app-server が利用できない場合の例外."""

    status_code = 503
    code = "backend_unavailable"

    def __init__(self, message: str = "Codex app-server に接続できません。") -> None:
        """バックエンド未接続の公開メッセージを設定する."""
        super().__init__(message=message)


class RpcTimeoutError(ApplicationError):
    """JSON-RPC 応答待ちタイムアウト時の例外."""

    status_code = 504
    code = "rpc_timeout"

    def __init__(self, *, request_id: int, method: str, timeout_sec: float) -> None:
        """タイムアウトした request の情報を補足する."""
        super().__init__(
            message="バックエンド応答がタイムアウトしました。",
            details={
                "requestId": request_id,
                "method": method,
                "timeoutSec": timeout_sec,
            },
        )


class RpcProtocolError(ApplicationError):
    """JSON-RPC プロトコル不整合時の例外."""

    status_code = 502
    code = "rpc_protocol_error"

    def __init__(self, message: str, *, payload: dict[str, Any] | None = None) -> None:
        """不整合内容を補足して初期化する."""
        super().__init__(message=message, details=payload)


class RpcResponseError(ApplicationError):
    """JSON-RPC `error` 応答を受け取った場合の例外."""

    status_code = 500
    code = "rpc_error"

    def __init__(self, *, request_id: int, method: str, error: dict[str, Any]) -> None:
        """上流の error 応答を補足情報に保持する."""
        super().__init__(
            message="バックエンドがエラーを返しました。",
            details={
                "requestId": request_id,
                "method": method,
                "error": error,
            },
        )
