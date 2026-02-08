# Task（実装タスク）

このドキュメントは「実装する内容」をタスク化して記載する。
ここでの「定義する」は、ドキュメント作成ではなく実装として定義することを指す。
仕様変更があれば内容を更新する。

## ドキュメント責務境界
- `design.md` を仕様の正本とし、要件・契約・制約は `design.md` に集約する
- `task.md` は実装手順と完了条件を管理し、仕様の再定義は行わない
- `design.md` と `task.md` が矛盾した場合は `design.md` を優先し、`task.md` を更新する

## 実装計画（チェックリスト）
- [x] 1. 開発環境を整備する
- [x] 1.1 Python 3.13+ / uv 前提を整備する
  - `uv sync` と `uv run ...` を開発標準として利用する
  - 設計参照: 影響範囲
  - 完了の定義: README に前提条件と開発コマンドが記載されている
- [x] 1.2 Codex CLI の認証手順を整備する
  - 通常ログイン / device auth / API キー方式を整理する
  - 認証情報を機密として扱う方針を明記する
  - 設計参照: 運用前提
  - 完了の定義: README に認証手順と機密情報の扱いが記載されている
- [x] 1.3 ローカル起動手順を整備する
  - `uv run uvicorn codex_httpd.main:app --reload` を開発起動手順にする
  - 設計参照: 影響範囲
  - 完了の定義: README の手順でローカル起動できる

- [x] 2. Docker 運用の土台を整備する
- [x] 2.1 Dockerfile と .dockerignore を整備する
  - 本番コンテナで API サーバーを起動できるようにする
  - 設計参照: 全体構成 / 影響範囲
  - 完了の定義: `docker build` と `docker run` で `/health` が 200 を返す
- [x] 2.2 Docker の環境変数と認証情報マウントを整備する
  - `CODEX_HTTPD_*`, `CODEX_BIN`, `CODEX_HOME` の運用を整理する
  - `auth.json` の read-only マウントを前提とする
  - 設計参照: 運用前提 / 非要件
  - 完了の定義: README と `.env.example` に反映されている
- [x] 2.3 Codex CLI バージョンを固定する
  - Docker 内の `@openai/codex` を固定バージョンでインストールする
  - 設計参照: 運用前提
  - 完了の定義: Dockerfile に固定バージョンが記載されている
- [ ] 2.4 HTTP 到達範囲をローカルホストに制限する
  - 非 Docker 起動時は `127.0.0.1` 待ち受けを既定にする
  - Docker 利用時も公開ポートをローカルホスト（`127.0.0.1`）へ制限する手順を明記する
  - 設計参照: 要件 > ネットワーク到達制限 / 運用前提
  - 完了の定義: ローカルホスト以外からアクセスできない設定で起動できる

- [ ] 3. API インターフェースの土台を実装する
- [ ] 3.1 ルーティング構成と依存注入を実装する
  - レイヤ境界（API / UseCase / Infrastructure）をコード構成に反映する
  - 依存方向 `API -> UseCase <- Infrastructure` を満たすように実装する
  - DI はコンストラクタ注入と `FastAPI Depends` で構成する
  - ルータは機能単位（`threads` / `turns` / `events` / `interrupt`）でファイル分割する
  - コントローラーは `api/routers/*.py` のエンドポイント関数として実装する
  - 依存解決は `api/dependencies.py` に集約し、コントローラー内で `new` しない
  - 依存オブジェクトの生成とライフサイクル管理は `main.py`（startup/shutdown）で行う
  - 共通エラーハンドリング・ログ出力の枠組みを入れる
  - 設計参照: アーキテクチャ方針 > レイヤ責務 / 依存方向 / DI 方針
  - 完了の定義: ルータ構成とレイヤ境界がコードに反映され、依存方向が保たれた状態でエンドポイント雛形が起動する
- [ ] 3.2 リクエスト/レスポンススキーマを実装する
  - `POST /threads`
  - `GET /threads`
  - `GET /threads/{threadId}`
  - `POST /threads/{threadId}/resume`
  - `POST /threads/{threadId}/turns`
  - `GET /threads/{threadId}/turns/{turnId}/events`
  - `POST /threads/{threadId}/turns/{turnId}/interrupt`
  - 設計参照: 仕様 / インターフェース > API
  - 完了の定義: 上記 API の入出力型がコードで定義され、テストで検証される
- [ ] 3.3 認証導入の拡張点を確保する
  - 現時点では認証ロジックは実装せず、API 層に後続導入可能な拡張点を残す
  - 認証方式（トークン種別・失効・配布）は後続タスクで決定する
  - 設計参照: 要件 > 認証拡張余地 / 非要件
  - 完了の定義: 認証方式を未確定のままでも、導入箇所が設計上明確になっている

- [ ] 4. Codex app-server 接続機能を実装する
- [ ] 4.1 app-server 子プロセス管理を実装する
  - 起動タイミングはアプリ起動時の即時起動（lazy 起動は採用しない）
  - 監視は FastAPI lifespan 配下のアプリ内バックグラウンドタスクで行う（supervisord は採用しない）
  - 異常終了時はアプリ内で自動再起動する
  - アプリ終了時は子プロセスを明示停止する
  - 起動・監視・終了・異常時復旧の流れを実装する
  - 設計参照: 仕様 / インターフェース > 全体構成 / アーキテクチャ方針 > レイヤ責務
  - 完了の定義: app-server の起動/停止がアプリライフサイクルで制御できる
- [ ] 4.2 JSON-RPC 中継クライアントを実装する
  - request/response/notification の送受信処理を実装する
  - HTTP リクエストと JSON-RPC request は `id` で 1:1 対応させる
  - response は `id` 一致で待ち合わせて返却する
  - notification は `threadId` / `turnId` 単位で SSE 配信対象へ振り分ける
  - 未知の notification は警告ログを出力して無視する
  - JSON-RPC `id` は `int64` 連番で採番する
  - `id` オーバーフローは実運用上は無視できる前提で運用する
  - JSON-RPC 応答待ちタイムアウト既定値は `120` 秒とする
  - JSON-RPC request の自動リトライは行わない（重複実行を避ける）
  - 設計参照: 仕様 / インターフェース > 全体構成 / アーキテクチャ方針 > レイヤ責務 / 依存方向
  - 完了の定義: JSON-RPC 呼び出しの成功/失敗を API 層で扱える

- [ ] 5. Thread API を実装する
- [ ] 5.1 `POST /threads` を実装する
  - `thread/start` を呼び、`threadId` を返す
  - 設計参照: 仕様 / インターフェース > API > Thread
  - 完了の定義: 正常系で `threadId` が返り、異常系が定義どおりに返る
- [ ] 5.2 `POST /threads/{threadId}/resume` を実装する
  - `thread/resume` を呼び、同一 `threadId` を返す
  - 設計参照: 仕様 / インターフェース > API > Thread
  - 完了の定義: 既存 thread 再開の正常系/異常系テストが通る
- [ ] 5.3 `GET /threads` を実装する
  - `thread/list` を透過呼び出しして結果を返す
  - API Server 独自の thread 一覧キャッシュ/永続化は持たない
  - 設計参照: 仕様 / インターフェース > API > Thread
  - 完了の定義: 一覧取得とページングパラメータのテストが通る
- [ ] 5.4 `GET /threads/{threadId}` を実装する
  - `thread/read` を透過呼び出しして結果を返す（`includeTurns` 対応）
  - 設計参照: 仕様 / インターフェース > API > Thread
  - 完了の定義: 詳細取得の正常系/異常系テストが通る

- [ ] 6. Turn 実行 API を実装する
- [ ] 6.1 `POST /threads/{threadId}/turns` の非ストリーミングを実装する
  - `stream=false` 時に `turnId` と `output` を返す
  - 設計参照: 仕様 / インターフェース > API > Turn
  - 完了の定義: 非ストリーミングの正常系/異常系テストが通る
- [ ] 6.2 `POST /threads/{threadId}/turns` のストリーミング開始を実装する
  - `stream=true` 時に `turnId` と `eventsUrl` を返す
  - 設計参照: 仕様 / インターフェース > API > Turn
  - 完了の定義: ストリーミング開始 API のテストが通る

- [ ] 6.3 会話専用の固定実行ポリシーを実装する
  - `approvalPolicy` / `sandbox` / `cwd` はサーバー設定値を常に使用し、HTTP リクエストからは上書きさせない
  - 設計参照: 要件 > 会話専用運用
  - 完了の定義: 実行ポリシーが固定化され、リクエスト側の任意上書きが無効化される

- [ ] 7. SSE イベント配信機能を実装する
- [ ] 7.1 `GET /threads/{threadId}/turns/{turnId}/events` を実装する
  - イベント種別・順序・`eventId`・再送保証・終端条件は `design.md` の Streaming 契約に厳密準拠する
  - 1接続あたり単一ライター + FIFO キューで配信順序を保証する
  - 設計参照: 仕様 / インターフェース > Streaming
  - 完了の定義: Streaming 契約（順序・終端・再送）のテストが通る
- [ ] 7.2 SSE 切断時の扱いを実装する
  - 無通信時に heartbeat（ping）イベントを定期送信する
  - heartbeat は接続維持/切断原因の切り分け目的であり、処理進捗保証には使わない
  - 接続切断を検知したら、SSE 配信キュー/購読を解放する
  - 接続切断時も turn 本体の実行は継続し、RPC を強制中断しない
  - 再接続時は先頭イベントから全再配信する
  - 再接続時は既送イベントの重複配信があり得る
  - 終端イベント重複受信時もクライアントが冪等処理できる契約を維持する
  - 設計参照: 仕様 / インターフェース > Streaming
  - 完了の定義: 切断時にリソースリークが発生せず、heartbeat 送信と切断検知のテストが通る

- [ ] 8. Cancel と rollback の整合機能を実装する
- [ ] 8.1 `POST /threads/{threadId}/turns/{turnId}/interrupt` を実装する
  - `turn/interrupt` 後に `thread/rollback(numTurns=1)` を実行する
  - 設計参照: 仕様 / インターフェース > 動作フロー（抜粋）
  - 完了の定義: キャンセル時に入力が履歴へ残らないことをテストで確認できる
- [ ] 8.2 rollback 失敗時のエラー通知を実装する
  - `thread/rollback` 失敗時は Codex app-server のエラー契約（`code` / `message` / `data`）に追従する
  - HTTP は `500` を返し、Codex 由来のエラー `code` / `message` を保持して返却する
  - SSE は終端 `error` を1回通知し、Codex 由来のエラー `code` / `message` を含める
  - ログは `ERROR` で `threadId` / `turnId` / `requestId` / `codexErrorCode` を出力する
  - 設計参照: 仕様 / インターフェース > エラーハンドリング
  - 完了の定義: rollback 失敗時の挙動がテストで再現・検証できる

- [ ] 9. 同時実行制御を実装する
- [ ] 9.1 同一 `threadId` の同時実行ポリシーを実装する
  - 同一 `threadId` の競合時は自動キャンセルせず `409 Conflict` を返す
  - 競合レスポンスには実行中 `turnId`（取得できる場合）を含める
  - 設計参照: 仕様 / インターフェース > 同時実行
  - 完了の定義: 競合時の挙動が仕様どおりで、テストが通る

- [ ] 10. エラー応答を実装する
- [ ] 10.1 HTTP エラー応答を実装する
  - `404` / `409` を設計方針に沿って返す
  - RPC タイムアウトは `504` を返す
  - app-server 未接続/異常終了は `503` を返す
  - JSON-RPC プロトコル不整合は `502` を返す
  - その他の内部失敗は `500` を返す
  - 設計参照: 仕様 / インターフェース > エラーハンドリング
  - 完了の定義: エラー種別ごとのレスポンステストが通る
- [ ] 10.2 SSE `error` 応答を実装する
  - app-server 異常終了・内部失敗を SSE `error` で通知する
  - 設計参照: 仕様 / インターフェース > エラーハンドリング
  - 完了の定義: SSE エラーイベントのテストが通る

- [ ] 11. テストを整備する
- [ ] 11.1 API の正常系/異常系テストを実装する
  - Thread/Turn/Interrupt の正常系と 404/409 異常系を網羅する
  - 設計参照: テスト方針
  - 完了の定義: API テストが CI で安定して通る
- [ ] 11.2 Cancel/rollback シナリオテストを実装する
  - キャンセル整合性（履歴に残らない）を検証する
  - 設計参照: テスト方針
  - 完了の定義: シナリオテストで整合性を再現確認できる
- [ ] 11.3 SSE イベント順序テストを実装する
  - `delta` から終端イベントまでの順序を検証する
  - 設計参照: テスト方針
  - 完了の定義: SSE 順序テストが安定して通る
