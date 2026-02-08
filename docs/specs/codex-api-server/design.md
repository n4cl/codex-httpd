# Design

## 概要
- Codex CLI（`codex app-server`）をバックエンドにした Codex API Server を提供する
- HTTP/SSE で外部から利用できる API を公開する
- Stateful / Streaming / Cancel をサポートする（Stateless は提供しない）
- 識別子は API Server 独自発行ではなく Codex 側の値（`threadId` / `turnId`）を利用する
- 本サーバーは Codex へのアクセス中継に専念し、永続化と利用者認証は担わない
- API Server 独自の thread 一覧/履歴ストアは持たず、Codex の `thread/list` / `thread/read` を透過中継する

## 目的 / 背景
- Codex CLI を HTTP 経由で利用できるようにする
- Codex は会話コンテキストを前提にした利用が中心であり、非対話的な単発入出力に最適化されていない
- セッション制約を踏まえ、会話を保持するモードに限定する
- 生成の中断と整合性（キャンセル時は履歴に残さない）を保証する

## ドキュメント責務境界
- `design.md` は仕様の正本（要件、制約、API 契約、運用前提）を定義する
- `task.md` は実装計画（作業分解、順序、完了条件）を定義する
- 仕様値（例: イベント契約、エラー契約、同時実行ポリシー）が不一致の場合は `design.md` を正とする
- `task.md` には仕様の再定義を増やさず、必要最小限の実装観点と `design.md` 参照を記載する

## 設計判断（妥当性評価）
- 妥当: Codex の実運用特性（対話前提）に合わせることで、API とバックエンドの意味差を減らせる
- 妥当: Stateless/Stateful の二重運用をやめ、実装・運用・テスト対象を絞れる
- 妥当: ID 名を Codex プロトコル（`threadId` / `turnId` / JSON-RPC `id`）に合わせることで変換コストを削減できる
- 妥当: 薄い HTTP ラッパーに合わせ、レイヤード + Ports/Adapters（Clean-lite）で責務分離と実装コストを両立する
- トレードオフ: Codex の ID 仕様変更の影響を直接受ける
- 前提: 本プロジェクトは Codex 固定（バックエンド差し替えは設計対象外）

## アーキテクチャ方針
### 採用方式
- レイヤード + Ports/Adapters（Clean-lite）を採用する
- フルのクリーンアーキテクチャは採用せず、薄いラッパーに必要な境界だけを実装する

### レイヤ責務
- API 層（FastAPI）: HTTP 入出力、バリデーション、レスポンス整形、SSE エンドポイントを担当する
- UseCase 層: `thread/start` や `turn/start` などのユースケース手順と整合性制御を担当する
- Infrastructure 層: `codex app-server` のプロセス管理、JSON-RPC 送受信、外部 I/O を担当する

### 依存方向
- 依存方向は `API -> UseCase <- Infrastructure` とする
- UseCase 層は `codex app-server` の具体実装に直接依存せず、Port（抽象）経由で利用する

### DI 方針
- DI 専用フレームワークは導入しない
- コンストラクタ注入と `FastAPI Depends` による Composition Root で依存を組み立てる

### ユースケース分割方針
- 初期は 1 API 主要操作につき 1 ユースケースを基本とする
- 次の条件に当てはまる場合はユースケースを分割する
  - 分岐や失敗パターンが増え、1 クラス/関数で見通しが悪くなる
  - 同じ手順が複数 API で再利用される
  - 単体テストで前提準備が過剰になる

### 非採用事項
- 将来未確定の差し替え前提での過剰抽象化は行わない
- 不要な DTO 変換層や広範囲なボイラープレートは追加しない

## 要件
- Stateful: thread を作成/再開し、以後は thread に対して turn を生成できる
- Streaming: SSE で逐次出力を配信できる
- Cancel: 実行中の生成を中断できる
- Cancel 時の整合性: キャンセルした入力は会話履歴に残さない
- 履歴参照: Codex が保持する thread の一覧/詳細を HTTP で参照できる
- 会話専用運用: 実行ポリシー（`approvalPolicy` / `sandbox` / `cwd`）はサーバー側で固定し、HTTP リクエストで上書きしない
- ネットワーク到達制限: API はローカルホスト（`127.0.0.1`）からの利用を前提に運用する
- 認証拡張余地: 現時点では詳細未確定だが、将来 API 認証を追加できる構成を維持する
- 識別子: `threadId` / `turnId` は Codex が返す ID をそのまま使う
- 追跡子: HTTP リクエストの `requestId` は Codex JSON-RPC の `id` に対応づける
- 永続化責務: `threadId` / `turnId` の長期保存はクライアント側で実装する

## 非要件
- 永続的な会話履歴の保存（DB 必須運用）はしない
- ユーザー管理・課金・高度な監査ログは範囲外
- Stateless API（単発生成専用エンドポイント）は提供しない
- API Server 独自の会話トークン発行・署名・期限管理は行わない
- Codex 以外のバックエンドへの抽象化・差し替えは行わない
- API クライアント向けの認証/認可（API キー、OAuth、セッション管理）は初期実装では行わない（方式は後続で決定する）

## 運用前提
- 個人利用を前提とし、HTTP 到達範囲はローカルホスト（`127.0.0.1`）に制限する
- サーバー側認証は現時点では未実装とし、将来導入を前提に設計する
- `codex` はサーバープロセス起動前に事前ログイン済み（同一ユーザー）であることを前提とする

## 仕様 / インターフェース
### 全体構成
- Codex API Server が HTTP API（REST + SSE）を提供する
- `codex app-server`（v2 プロトコル）を子プロセスとして常駐起動し、stdio の JSON-RPC を中継する
- turn 実行管理（中断・イベント中継）を API Server が担う

### ストレージ方針
- `threadId` は Codex `thread/start` または `thread/resume` が返す `thread.id` を利用する
- `turnId` は Codex `turn/start` が返す `turn.id` を利用する
- 実行中 turn の状態はメモリで保持する（プロセス再起動で消失）
- `requestId` は HTTP 境界で採番し、Codex JSON-RPC `id` と相互参照可能にする
- 永続ストア（DB/ファイル）への保存は行わない。必要な永続化はクライアント側で実施する
- Thread 一覧は API Server で独自管理せず、都度 Codex `thread/list` に問い合わせる

### 用語
- Thread: Stateful の会話単位。`threadId` は Codex `thread.id`
- Turn: 1 回の生成単位。`turnId` は Codex `turn.id`
- Request: 1 回の JSON-RPC 呼び出し単位。`requestId` は JSON-RPC `id`

### API
#### Thread
- `POST /threads`
  - 新規 thread を作成する
  - Codex `thread/start` を呼び、`threadId`（=`thread.id`）を返す
- `POST /threads/{threadId}/resume`
  - 既存 thread を再開する
  - Codex `thread/resume` を呼び、`threadId` を返す（同一 ID）
- `GET /threads`
  - thread 一覧を取得する
  - Codex `thread/list` を呼ぶ（`cursor` / `limit` / `sortKey` / `sourceKinds` などは透過）
- `GET /threads/{threadId}`
  - 指定 thread の詳細を取得する
  - Codex `thread/read` を呼ぶ（`includeTurns` を透過）

#### Turn
- `POST /threads/{threadId}/turns`
  - 指定 thread に対して生成（turn）を開始する
  - Codex `turn/start` を呼ぶ
  - `stream=false`: `turnId` と `output` を返す
  - `stream=true`: `turnId` と `eventsUrl` を返す

#### Streaming
- `GET /threads/{threadId}/turns/{turnId}/events`（SSE）
  - 指定 turn のイベントを SSE で取得する
  - `delta`: Codex `agent_message_delta` を中継（`itemId` を保持）
  - `final`: Codex `turn/completed` かつ `turn.status=completed`
  - `cancelled`: Codex `turn/completed` かつ `turn.status=interrupted`
  - `error`: Codex `error` または `turn/completed` かつ `turn.status=failed`
  - 1つの SSE 接続内では先頭から順序どおり配信する
  - 各イベントに `eventId`（SSE `id`）を付与する
  - 配信保証は `at-least-once`（重複配信あり）とする
  - 再接続時は先頭イベントから全再配信する（途中再開は行わない）
  - 終端イベント（`final` / `cancelled` / `error`）は1接続内で1回のみ配信する
  - 再接続時の重複受信に備え、クライアントは終端イベントを冪等に扱う

#### Cancel
- `POST /threads/{threadId}/turns/{turnId}/interrupt`
  - 実行中の turn を中断する
  - Codex `turn/interrupt` を呼ぶ（`threadId` と `turnId` の両方が必須）

### 動作フロー（抜粋）
- Stateful（完了）
  - `POST /threads` → `POST /threads/{threadId}/turns` → `turnId` 取得 →
    SSE 中継 → `turn/completed(completed)` → `final`
- Stateful（キャンセル）
  - `POST /threads/{threadId}/turns/{turnId}/interrupt` → `turn/interrupt` →
    `turn/completed(interrupted)` → `thread/rollback(numTurns=1)` → `cancelled`

### 同時実行
- 同一 `threadId` は同時に 1 `turn` までとする
  - 競合時は自動中断せず `409` を返す（取得できる場合は実行中 `turnId` を含める）

### エラーハンドリング
- `threadId` 不正/未知: 404
- `turnId` 不正/未知、または `threadId` との不整合: 404
- 同一 `threadId` の同時実行制約違反: 409
- app-server 異常終了: `error` を SSE に通知
- rollback 失敗: `error`（会話整合性を保証できない）

## 影響範囲
- Codex API Server のプロセス管理（`codex app-server`）
- Codex ID（`threadId` / `turnId` / `requestId`）の受け渡し
- メモリ上の turn 管理と SSE のイベント中継

## リスク / 代替案
- メモリ管理のため、プロセス再起動で実行中 turn が失われる
- rollback 失敗時の整合性保証が難しいため、運用での監視が必要
- サーバー側で利用者認証を行わないため、公開ネットワークに露出すると不正利用リスクが高い

## テスト方針
- Stateful API の正常系/異常系（404/409）を網羅する
- Cancel/rollback の整合性をシナリオテストで確認する
- SSE のストリーミングイベント順序を検証する
