# Design

## 概要
- Codex CLI（`codex app-server`）をバックエンドにした Codex API Server を提供する
- HTTP/SSE で外部から利用できる API を公開する
- Stateful / Streaming / Cancel をサポートする（Stateless は提供しない）
- 識別子は API Server 独自発行ではなく Codex 側の値（`threadId` / `turnId`）を利用する
- 本サーバーは Codex へのアクセス中継に専念し、永続化と利用者認証は担わない

## 目的 / 背景
- Codex CLI を HTTP 経由で利用できるようにする
- Codex は会話コンテキストを前提にした利用が中心であり、非対話的な単発入出力に最適化されていない
- セッション制約を踏まえ、会話を保持するモードに限定する
- 生成の中断と整合性（キャンセル時は履歴に残さない）を保証する

## 設計判断（妥当性評価）
- 妥当: Codex の実運用特性（対話前提）に合わせることで、API とバックエンドの意味差を減らせる
- 妥当: Stateless/Stateful の二重運用をやめ、実装・運用・テスト対象を絞れる
- 妥当: ID 名を Codex プロトコル（`threadId` / `turnId` / JSON-RPC `id`）に合わせることで変換コストを削減できる
- トレードオフ: Codex の ID 仕様変更の影響を直接受ける
- 前提: 本プロジェクトは Codex 固定（バックエンド差し替えは設計対象外）

## 要件
- Stateful: thread を作成/再開し、以後は thread に対して turn を生成できる
- Streaming: SSE で逐次出力を配信できる
- Cancel: 実行中の生成を中断できる
- Cancel 時の整合性: キャンセルした入力は会話履歴に残さない
- 識別子: `threadId` / `turnId` は Codex が返す ID をそのまま使う
- 追跡子: HTTP リクエストの `requestId` は Codex JSON-RPC の `id` に対応づける
- 永続化責務: `threadId` / `turnId` の長期保存はクライアント側で実装する

## 非要件
- 永続的な会話履歴の保存（DB 必須運用）はしない
- ユーザー管理・課金・高度な監査ログは範囲外
- Stateless API（単発生成専用エンドポイント）は提供しない
- API Server 独自の会話トークン発行・署名・期限管理は行わない
- Codex 以外のバックエンドへの抽象化・差し替えは行わない
- API クライアント向けの認証/認可（API キー、OAuth、セッション管理）は実装しない

## 運用前提
- 個人利用を前提とし、サーバー側で利用者認証は行わない
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
- 同一 `threadId` は同時に 1 `turn` までを推奨
  - 既存 turn を自動中断、または 409 を返す

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
- SSE 切断時の再接続仕様を別途検討する必要がある
- rollback 失敗時の整合性保証が難しいため、運用での監視が必要
- サーバー側で利用者認証を行わないため、公開ネットワークに露出すると不正利用リスクが高い

## テスト方針
- Stateful API の正常系/異常系（404/409）を網羅する
- Cancel/rollback の整合性をシナリオテストで確認する
- SSE のストリーミングイベント順序を検証する
