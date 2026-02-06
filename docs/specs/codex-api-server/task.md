# Task（実装タスク）

このドキュメントは「実装する内容」をタスク化して記載する。
ここでの「定義する」は、ドキュメント作成ではなく実装として定義することを指す。
仕様変更があれば内容を更新する。

## 進め方
- タスクは実装して初めて完了とする（実装・検証まで含める）
- ドキュメントは補助として更新するが、完了条件はコードとテストで満たす

## 実装計画（チェックリスト）
- [x] 1. ローカル開発セットアップ
- [x] 1.1 Python 3.13+ と uv の利用方針を明文化する
  - 前提: Python 3.13+ と uv をインストールする
  - セットアップ: `uv sync` で .venv 作成と依存導入を行う
  - 開発コマンドは `uv run ...` を標準とする（ruff/pytest/uvicorn など）
  - _Design ref: 影響範囲_
  - 完了の定義: 前提バージョン、`uv sync`、`uv run` 運用がドキュメントに明記されている
- [x] 1.2 Codex CLI の前提と導入方法を整理する
  - `codex` コマンドがローカルで利用できることを前提（導入方法は環境に合わせて選択）
  - 初回ログイン: `codex` 起動時に ChatGPT アカウントで認証（API キー不要）
  - ヘッドレス/CLI 環境: `codex login --device-auth` を利用する
  - 自動化/CI: API キー方式も許容し、必要に応じて `codex login --with-api-key` を利用する
  - 認証キャッシュ: `~/.codex/auth.json` または OS の credential store に保存
  - ローカル開発での扱い: `auth.json` は機密情報として扱い、リポジトリに含めない
  - _Design ref: 影響範囲_
  - 完了の定義: 認証手順（通常/ヘッドレス/APIキー）と機密情報の扱いがドキュメントに明記されている
- [x] 1.3 開発起動手順の最小セットを定義する
  - 手順: `uv sync` → `uv run uvicorn codex_httpd.main:app --reload`
  - _Design ref: 影響範囲_
  - 完了の定義: ローカル起動コマンドがドキュメントに記載され、手順が 1 つに統一されている

- [x] 2. Docker 運用設計
- [x] 2.1 本番 Docker の起動方式を決める
  - `codex app-server` と FastAPI の同一コンテナ運用
  - `_Design ref: 影響範囲`
  - 完了の定義: Docker 運用方針として同一コンテナ運用が明記されている
- [x] 2.2 環境変数/設定の管理方針を定義する
  - 運用パラメータは以下で統一する
  - `CODEX_HTTPD_HOST`（任意, 既定値: `0.0.0.0`）: FastAPI の bind host
  - `CODEX_HTTPD_PORT`（任意, 既定値: `8000`）: FastAPI の listen port
  - `CODEX_HTTPD_LOG_LEVEL`（任意, 既定値: `info`）: API Server のログレベル
  - `CODEX_HTTPD_APP_SERVER_STARTUP_TIMEOUT_SEC`（任意, 既定値: `15`）: `codex app-server` 起動待ちタイムアウト（秒）
  - `CODEX_HTTPD_RPC_TIMEOUT_SEC`（任意, 既定値: `60`）: JSON-RPC 応答待ちタイムアウト（秒）
  - `CODEX_BIN`（任意, 既定値: `codex`）: Codex CLI 実行バイナリ名/パス
  - `CODEX_HOME`（必須, 既定値なし）: 認証情報 `auth.json` を含む Codex のホームディレクトリ
  - `CODEX_HOME/auth.json` は read-only マウントを必須とする
  - 本サーバーは利用者認証・独自トークン管理を行わない（関連設定は追加しない）
  - `_Design ref: 運用前提 / 非要件 / 仕様 / インターフェース > 全体構成`
  - 完了の定義: 設定項目ごとに「変数名・既定値・必須/任意・用途」を一覧化し、非要件が併記されている
- [x] 2.3 Docker 内のセットアップ方針を定義する
  - ベースイメージは `python:3.13-slim` を採用する
  - OS パッケージは最小構成（`ca-certificates` など）に限定する
  - `uv` で依存を導入する（`uv sync --frozen --no-dev`）
  - Codex CLI はコンテナ内に導入し、`CODEX_BIN=codex` で実行可能にする
  - 非 root ユーザーでアプリを実行する
  - `CODEX_HOME` をコンテナ内で固定し、`auth.json` を read-only でマウントする
  - 起動コマンドは `uv run uvicorn codex_httpd.main:app --host ${CODEX_HTTPD_HOST} --port ${CODEX_HTTPD_PORT}` を基準とする
  - ヘルスチェックは `GET /health` で判定する
  - `_Design ref: 運用前提 / 影響範囲`
  - 完了の定義: Dockerfile または運用ドキュメントに、CLI 導入手順と認証情報の read-only マウント手順が記載されている

- [ ] 3. API 仕様の確定とスキーマ整理
- [ ] 3.1 リクエスト/レスポンスの JSON スキーマを定義する
  - `POST /threads`
  - リクエスト: 空ボディ
  - レスポンス: `200 OK` `{"threadId": string, "requestId": string}`
  - `POST /threads/{threadId}/resume`
  - リクエスト: 空ボディ
  - レスポンス: `200 OK` `{"threadId": string, "requestId": string}`
  - `POST /threads/{threadId}/turns`
  - リクエスト: `{"input": string, "stream"?: boolean}`（`stream` 既定値: `false`）
  - レスポンス（`stream=false`）: `200 OK` `{"turnId": string, "output": string, "requestId": string}`
  - レスポンス（`stream=true`）: `200 OK` `{"turnId": string, "eventsUrl": string, "requestId": string}`
  - `GET /threads/{threadId}/turns/{turnId}/events`
  - レスポンス: `200 OK` `text/event-stream`
  - `POST /threads/{threadId}/turns/{turnId}/interrupt`
  - リクエスト: 空ボディ
  - レスポンス: `200 OK` `{"turnId": string, "requestId": string}`
  - 設計: 完了
  - 実装/検証: 未着手
  - `_Design ref: 仕様 / インターフェース > API`
  - 完了の定義: 全エンドポイントについてリクエスト/レスポンスの必須項目、型、ステータスコードが定義されている
- [ ] 3.2 SSE イベント形式と順序を定義する (C)
  - `delta` / `final` / `cancelled` / `error`
  - `_Design ref: 仕様 / インターフェース > Streaming`
  - 完了の定義: 各イベントの JSON 形式と発火順序、終端イベント（`final`/`cancelled`/`error`）の条件が定義されている
- [ ] 3.3 エラー応答の方針を定義する (C)
  - 404/409 と SSE `error` の扱いを明文化
  - `_Design ref: 仕様 / インターフェース > エラーハンドリング`
  - 完了の定義: エラー種別ごとに HTTP ステータス、エラーコード、メッセージ方針が定義されている

- [ ] 4. Codex app-server 連携の詳細設計
- [ ] 4.1 子プロセス起動/終了/再起動の方針を決める (C)
  - 方針: 起動時に常駐、異常終了時の再起動戦略
  - `_Design ref: 仕様 / インターフェース > 全体構成`
  - 完了の定義: 起動・正常終了・異常終了・再起動時の状態遷移と運用ルールが定義されている
- [ ] 4.2 JSON-RPC 中継のプロトコルを定義する (C)
  - 送受信のメッセージ種別とエラー処理
  - `_Design ref: 仕様 / インターフェース > 全体構成`
  - 完了の定義: JSON-RPC の request/response/notification の取り扱いと、失敗時の変換ルールが定義されている

- [ ] 5. 識別子設計（Codex ID / requestId）
- [ ] 5.1 `threadId` / `turnId` の受け渡しルールを定義する (C)
  - Codex が返す ID をそのまま API 境界で扱う
  - `_Design ref: 要件 / 仕様 / インターフェース > ストレージ方針`
  - 完了の定義: API 入出力での ID 名称、必須条件、不整合時の扱いが定義されている
- [ ] 5.2 `requestId` の採番・相互参照ルールを定義する (C)
  - HTTP リクエストと Codex JSON-RPC `id` の対応を保証する
  - `_Design ref: 要件 / 仕様 / インターフェース > ストレージ方針`
  - 完了の定義: `requestId` の採番方式、重複回避、ログ追跡方法が定義されている

- [ ] 6. Turn 管理と SSE 中継
- [ ] 6.1 turn のメモリ保持構造を定義する (C)
  - `turnId` と状態、SSE キューの設計
  - `_Design ref: 仕様 / インターフェース > ストレージ方針`
  - 完了の定義: 保持する状態項目、ライフサイクル、破棄条件が定義されている
- [ ] 6.2 SSE ストリーミングの接続/切断方針を決める (C)
  - 切断時の扱い、再接続の扱い
  - `_Design ref: リスク / 代替案`
  - 完了の定義: 接続開始・切断・タイムアウト・再接続可否の仕様が定義されている

- [ ] 7. Stateful フローの整合性（キャンセル）
- [ ] 7.1 `turn/interrupt` と `thread/rollback` の順序を確定する (C)
  - 中断時に履歴を残さないことを保証する
  - `_Design ref: 仕様 / インターフェース > 動作フロー（抜粋）`
  - 完了の定義: キャンセル時の呼び出し順序と、履歴非残存を保証する条件が定義されている
- [ ] 7.2 rollback 失敗時の扱いを定義する (C)
  - SSE で error を通知する条件
  - `_Design ref: 仕様 / インターフェース > エラーハンドリング`
  - 完了の定義: rollback 失敗時のクライアント通知、ログ、運用対応が定義されている

- [ ] 8. 同時実行ルール
- [ ] 8.1 同一 `threadId` の同時実行ポリシーを決定する (C)
  - 自動キャンセル or 409
  - `_Design ref: 仕様 / インターフェース > 同時実行`
  - 完了の定義: 採用ポリシーが 1 つに確定し、競合時のレスポンス仕様が定義されている

- [ ] 9. FastAPI の構成方針
- [ ] 9.1 ルーティング構成と依存注入方針を決める (C)
  - ルータ分割と共通処理（エラーハンドリング/ログ）
  - `_Design ref: 仕様 / インターフェース > API`
  - 完了の定義: ルータ構成、依存注入ポイント、共通処理の責務分離が定義されている
- [ ] 9.2 SSE 実装方針を決める (C)
  - FastAPI での SSE 実装方式を確定
  - `_Design ref: 仕様 / インターフェース > Streaming`
  - 完了の定義: SSE 実装方式（レスポンス生成、flush、切断検知、終端処理）が定義されている

- [ ] 10. テスト設計
- [ ] 10.1 API 正常系/異常系のテスト観点を洗い出す (C)
  - 404/409 と SSE `error` を含める
  - `_Design ref: テスト方針`
  - 完了の定義: エンドポイント別のテストマトリクス（正常/異常）が作成されている
- [ ] 10.2 Cancel/rollback のシナリオテスト方針を決める (C)
  - `_Design ref: テスト方針`
  - 完了の定義: キャンセル時の rollback 実行と履歴整合性を検証するシナリオが定義されている
- [ ] 10.3 SSE イベント順序の検証方針を決める (C)
  - `_Design ref: テスト方針`
  - 完了の定義: `delta` から終端イベントまでの順序と終端一意性を検証する観点が定義されている
