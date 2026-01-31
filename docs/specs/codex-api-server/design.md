# Design

## 概要
- Codex CLI（`codex app-server`）をバックエンドにした Codex API Server を提供する
- HTTP/SSE で外部から利用できる API を公開する
- Stateless / Stateful / Streaming / Cancel をサポートする

## 目的 / 背景
- Codex CLI を HTTP 経由で利用できるようにする
- 会話履歴を外部管理するモードと、会話を保持するモードの両方を提供する
- 生成の中断と整合性（キャンセル時は履歴に残さない）を保証する

## 要件
- Stateless: 入力 `messages` を渡して単発生成できる
- Stateful: conversation を作成し、以後は会話に対して生成できる
- Streaming: SSE で逐次出力を配信できる
- Cancel: 実行中の生成を中断できる
- Cancel 時の整合性: キャンセルした入力は会話履歴に残さない

## 非要件
- 永続的な会話履歴の保存（DB 必須運用）はしない
- ユーザー管理・課金・高度な監査ログは範囲外

## 仕様 / インターフェース
### 全体構成
- Codex API Server が HTTP API（REST + SSE）を提供する
- `codex app-server` を子プロセスとして常駐起動し、stdio の JSONL を中継する
- Run 管理（キャンセル・イベント中継）を API Server が担う

### ストレージ方針
- 会話識別子は署名トークン（不透明トークン）で発行する
  - `threadId` と `exp` を含め、署名検証で改ざんを防ぐ
- Run 管理はメモリで保持する（プロセス再起動で消失）

### 用語
- Conversation: Stateful の会話単位。`conversationId`（署名トークン）として発行する
- Response: Stateless の単発生成
- Run: ストリーミングとキャンセルの単位。`runId` を発行する

### API
#### Stateless
- `POST /responses`
  - `stream=false`: 単発で `output` を返す
  - `stream=true`: `runId` と `eventsUrl` を返す

#### Stateful
- `POST /conversations`
  - `conversationId` と `expiresAt` を返す
- `POST /conversations/{conversationId}/responses`
  - `stream=false`: `output` を返す
  - `stream=true`: `runId` と `eventsUrl` を返す

#### Streaming
- `GET /runs/{runId}/events`（SSE）
  - `delta` / `final` / `cancelled` / `error`

#### Cancel
- `POST /runs/{runId}/cancel`

### 動作フロー（抜粋）
- Stateless
  - `POST /responses (stream=true)` → `runId` 発行 → SSE 中継 → `final` or `cancelled`
- Stateful（完了）
  - `POST /conversations` → `POST /conversations/{id}/responses` → `turn/start` → `final`
- Stateful（キャンセル）
  - `POST /runs/{runId}/cancel` → `turn/interrupt` → `turn/completed(interrupted)` →
    `thread/rollback(n=1)` → `cancelled`

### 同時実行
- 同一 conversation は同時に 1 run までを推奨
  - 既存 run を自動キャンセル、または 409 を返す

### トークン設計
- payload: `threadId`, `exp`, `scope=conversation`
- 有効期限切れは 401/410 で `POST /conversations` を促す

### エラーハンドリング
- `conversationId` 不正/期限切れ: 401/410
- `runId` 不正: 404
- app-server 異常終了: `error` を SSE に通知
- rollback 失敗: `error`（会話整合性を保証できない）

## 影響範囲
- Codex API Server のプロセス管理（`codex app-server`）
- conversation トークンの発行・検証
- メモリ上の run 管理と SSE のイベント中継

## リスク / 代替案
- メモリ管理のため、プロセス再起動で run が失われる
- SSE 切断時の再接続仕様を別途検討する必要がある
- rollback 失敗時の整合性保証が難しいため、運用での監視が必要

## テスト方針
- API の正常系/異常系（401/404/410/409）を網羅する
- Cancel/rollback の整合性をシナリオテストで確認する
- SSE のストリーミングイベント順序を検証する
