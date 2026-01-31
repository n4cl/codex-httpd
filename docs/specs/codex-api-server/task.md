# Task（詳細設計）

このドキュメントは「あるべき姿（詳細設計）」を記載する。
仕様変更があれば内容を更新する。

## 実装計画（チェックリスト）
- [x] 1. ローカル開発セットアップ
- [x] 1.1 Python 3.13+ と uv の利用方針を明文化する
  - 前提: Python 3.13+ と uv をインストールする
  - セットアップ: `uv sync` で .venv 作成と依存導入を行う
  - 開発コマンドは `uv run ...` を標準とする（ruff/pytest/uvicorn など）
  - _Design ref: 影響範囲_
- [x] 1.2 Codex CLI の前提と導入方法を整理する
  - `codex` コマンドがローカルで利用できることを前提（導入方法は環境に合わせて選択）
  - 初回ログイン: `codex` 起動時に ChatGPT アカウントで認証（API キー不要）
  - ヘッドレス/CLI 環境: `codex login --device-auth` を利用する
  - 自動化/CI: API キー方式も許容し、必要に応じて `codex login --with-api-key` を利用する
  - 認証キャッシュ: `~/.codex/auth.json` または OS の credential store に保存
  - ローカル開発での扱い: `auth.json` は機密情報として扱い、リポジトリに含めない
  - _Design ref: 影響範囲_
- [x] 1.3 開発起動手順の最小セットを定義する
  - 手順: `uv sync` → `uv run uvicorn codex_httpd.main:app --reload`
  - _Design ref: 影響範囲_

- [ ] 2. Docker 運用設計
- [x] 2.1 本番 Docker の起動方式を決める
  - `codex app-server` と FastAPI の同一コンテナ運用
  - `_Design ref: 影響範囲`
- [ ] 2.2 環境変数/設定の管理方針を定義する (C)
  - トークン署名鍵や TTL など
  - `_Design ref: 仕様 / インターフェース > トークン設計`
- [ ] 2.3 Docker 内のセットアップ方針を定義する (C)
  - Codex CLI と必要パッケージのインストール方法を確定
  - 認証情報の再利用方針: `cli_auth_credentials_store = "file"` を指定し、`CODEX_HOME` 配下の `auth.json` を read-only でマウントして利用する
  - `_Design ref: 影響範囲`

- [ ] 3. API 仕様の確定とスキーマ整理
- [ ] 3.1 リクエスト/レスポンスの JSON スキーマを定義する (C)
  - `POST /responses` / `POST /conversations` / `POST /conversations/{id}/responses`
  - `_Design ref: 仕様 / インターフェース > API`
- [ ] 3.2 SSE イベント形式と順序を定義する (C)
  - `delta` / `final` / `cancelled` / `error`
  - `_Design ref: 仕様 / インターフェース > Streaming`
- [ ] 3.3 エラー応答の方針を定義する (C)
  - 401/404/410/409 の扱いを明文化
  - `_Design ref: 仕様 / インターフェース > エラーハンドリング`

- [ ] 4. Codex app-server 連携の詳細設計
- [ ] 4.1 子プロセス起動/終了/再起動の方針を決める (C)
  - 方針: 起動時に常駐、異常終了時の再起動戦略
  - `_Design ref: 仕様 / インターフェース > 全体構成`
- [ ] 4.2 JSONL 中継のプロトコルを定義する (C)
  - 送受信のメッセージ種別とエラー処理
  - `_Design ref: 仕様 / インターフェース > 全体構成`

- [ ] 5. Conversation トークン設計
- [ ] 5.1 署名トークンの payload と有効期限を定義する (C)
  - `threadId`, `exp`, `scope=conversation`
  - `_Design ref: 仕様 / インターフェース > トークン設計`
- [ ] 5.2 期限切れ時のエラー応答を確定する (C)
  - 401/410 の使い分け
  - `_Design ref: 仕様 / インターフェース > トークン設計`

- [ ] 6. Run 管理と SSE 中継
- [ ] 6.1 run のメモリ保持構造を定義する (C)
  - `runId` と状態、SSE キューの設計
  - `_Design ref: 仕様 / インターフェース > ストレージ方針`
- [ ] 6.2 SSE ストリーミングの接続/切断方針を決める (C)
  - 切断時の扱い、再接続の扱い
  - `_Design ref: リスク / 代替案`

- [ ] 7. Stateful フローの整合性（キャンセル）
- [ ] 7.1 `turn/interrupt` と `thread/rollback` の順序を確定する (C)
  - 中断時に履歴を残さないことを保証する
  - `_Design ref: 仕様 / インターフェース > 動作フロー（抜粋）`
- [ ] 7.2 rollback 失敗時の扱いを定義する (C)
  - SSE で error を通知する条件
  - `_Design ref: 仕様 / インターフェース > エラーハンドリング`

- [ ] 8. 同時実行ルール
- [ ] 8.1 同一 conversation の同時実行ポリシーを決定する (C)
  - 自動キャンセル or 409
  - `_Design ref: 仕様 / インターフェース > 同時実行`

- [ ] 9. FastAPI の構成方針
- [ ] 9.1 ルーティング構成と依存注入方針を決める (C)
  - ルータ分割と共通処理（auth/ログ）
  - `_Design ref: 仕様 / インターフェース > API`
- [ ] 9.2 SSE 実装方針を決める (C)
  - FastAPI での SSE 実装方式を確定
  - `_Design ref: 仕様 / インターフェース > Streaming`

- [ ] 10. テスト設計
- [ ] 10.1 API 正常系/異常系のテスト観点を洗い出す (C)
  - 401/404/410/409 を含める
  - `_Design ref: テスト方針`
- [ ] 10.2 Cancel/rollback のシナリオテスト方針を決める (C)
  - `_Design ref: テスト方針`
- [ ] 10.3 SSE イベント順序の検証方針を決める (C)
  - `_Design ref: テスト方針`
