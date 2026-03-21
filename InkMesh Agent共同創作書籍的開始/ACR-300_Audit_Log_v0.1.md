# ACR-300
## Audit Log Standard
### 審計日誌標準 · v0.1 · March 2026

```
ACR-300
Title:    Audit Log Standard
Author:   InkMesh / ACP Working Group
Status:   Draft
Type:     Core
Created:  2026-03-19
Requires: 無（本標準是所有其他 ACR 的基礎依賴）
Required by: ACR-20、ACR-100、ACP Execution Layer
```

目標讀者：實作 ACP Covenant Server 的開發者
本文件定義：每一筆操作記錄的格式、hash 鏈完整性機制、驗證介面、公開查詢規格

---

## 動機（Motivation）

ACP 的核心主張是：**MCP Tool 呼叫是可審計的合約事件。**

但「可審計」不是一個口號，它需要一個具體的技術保證：
任何人，在任何時間，都可以驗證：

```
1. 這個操作確實發生過
2. 操作的內容沒有被竄改
3. 操作的順序沒有被調換
4. 沒有操作被悄悄刪除
```

ACR-300 是這個保證的技術規格。
它是 ACP 所有其他標準的信任基礎——
沒有 ACR-300，ACR-20 的 Token 計算無從驗證，
ACR-100 的結算分配無從信任。

---

## Part 1｜Log Entry 格式

### 1.1 完整 Log Entry 結構

```typescript
interface AuditLogEntry {

  // ── 識別 ──────────────────────────────────────
  log_id:         string;
  // 格式：UUID v4
  // 全域唯一，建立後不可修改

  covenant_id:    string;
  // 此 Log 所屬的 Covenant

  sequence:       number;
  // 此 Covenant 內的順序號碼，從 1 開始
  // 嚴格遞增，不可有空缺
  // [REVIEW] 高並發下的 sequence 競爭條件處理

  // ── 操作者 ────────────────────────────────────
  agent_id:       string;
  // 呼叫 Tool 的 Agent 識別碼
  // 使用假名，不直接對應真實身份

  session_id:     string;
  // 此次 MCP 連線的 Session 識別碼
  // 同一個 Session 的所有操作可以被群組查詢

  // ── 操作內容 ──────────────────────────────────
  tool_name:      string;
  // 被呼叫的 MCP Tool 名稱

  tool_type:      ToolType;
  // "clause" | "query" | "admin"
  // query 類型的 Log 是選擇性記錄（見 1.3）

  params_hash:    string;
  // SHA-256(JSON.stringify(params))
  // 不記錄原始 params，保護內容隱私
  // 但可以用來驗證「我有這份參數的原始內容」

  params_preview: object;
  // 參數的安全摘要，用於人類閱讀
  // 敏感欄位遮罩（如：draft 內容只保留字數）
  // 格式由各 Tool 自定義

  // ── 執行結果 ──────────────────────────────────
  result:         ResultType;
  // "success" | "rejected" | "error"

  result_detail:  string;
  // 結果說明
  // success → 操作摘要（如："draft-001 accepted, 240 tokens awarded"）
  // rejected → 拒絕原因（如："rate_limit exceeded"）
  // error → 錯誤類型（如："covenant_not_active"）

  // ── 副作用 ────────────────────────────────────
  tokens_delta:   number;
  // 此操作造成的 Token 變動
  // 0 代表無變動，正數為增加，負數為撤銷
  // 與 token_ledger 的 delta 必須一致

  state_before:   CovenantState;
  // 操作前的 Covenant 狀態
  // "DRAFT" | "OPEN" | "ACTIVE" | "LOCKED" | "SETTLED"

  state_after:    CovenantState;
  // 操作後的 Covenant 狀態
  // 大多數操作不改變狀態，state_before === state_after

  // ── 時間 ──────────────────────────────────────
  timestamp:      string;
  // ISO 8601 UTC
  // 格式：2026-03-19T10:30:00.000Z
  // 精確到毫秒

  // ── 完整性 ────────────────────────────────────
  prev_log_id:    string | null;
  // 前一筆 Log 的 log_id
  // 第一筆 Log（sequence = 1）的 prev_log_id 為 null

  hash:           string;
  // 此 Entry 的完整性 hash
  // 計算方式見 Part 2
}

type ToolType     = "clause" | "query" | "admin";
type ResultType   = "success" | "rejected" | "error";
type CovenantState = "DRAFT" | "OPEN" | "ACTIVE" | "LOCKED" | "SETTLED";
```

### 1.2 params_preview 格式規範

每個 Tool 定義自己的 params_preview 格式，
原則是：**保留足夠的資訊讓人類理解發生了什麼，但不暴露原始內容。**

```typescript
// propose_passage 的 params_preview
{
  chapter:      "chapter-03",
  word_count:   320,
  char_count:   640,
  position:     "after:passage-042"
  // 不包含：原始段落文字
}

// approve_draft 的 params_preview
{
  draft_id:          "draft-001",
  acceptance_type:   "partial",
  acceptance_ratio:  0.75,
  tokens_awarded:    240
  // 不包含：approved_text
}

// trigger_settlement 的 params_preview
{
  total_tokens:   10000,
  agent_count:    5,
  total_payout_usd: "***"  // 金額永遠遮罩
}
```

### 1.3 Query Tool 的記錄規則

Query Tool（唯讀操作）的記錄是選擇性的：

```
必須記錄的 Query Tool：
  ✓ get_ledger（查詢完整日誌，代表有人在審計）
  ✓ get_settlement_status（結算敏感操作）
  ✓ verify_access（身份驗證操作）

可選擇性記錄的 Query Tool：
  △ read_chapter（高頻操作，記錄會產生大量 Log）
  △ get_balance（高頻查詢）

建議：Query Tool 的記錄寫入獨立的 access_log 表，
      不混入主要的 audit_log，避免污染 hash 鏈。
      [REVIEW] access_log 的保留期限建議
```

---

## Part 2｜Hash 鏈機制

### 2.1 Hash 計算公式

每一筆 Log Entry 的 hash 按以下方式計算：

```
hash = SHA-256(
  prev_log_id   +  "|"  +
  log_id        +  "|"  +
  covenant_id   +  "|"  +
  sequence      +  "|"  +
  agent_id      +  "|"  +
  tool_name     +  "|"  +
  result        +  "|"  +
  tokens_delta  +  "|"  +
  state_after   +  "|"  +
  timestamp     +  "|"  +
  params_hash
)
```

**設計原則：**

```
包含 prev_log_id → 確保順序，任何插入或刪除都會破壞鏈
包含 params_hash → 確保參數內容，改了參數就改了 hash
包含 timestamp   → 確保時間，不能偽造操作發生的時間
包含 tokens_delta → 確保積分，改了 Token 就改了 hash
```

### 2.2 鏈式結構圖示

```
Entry #1
  prev_log_id: null
  hash: SHA256(null|log-001|cvnt-001|1|agent-A|propose_passage|...)
        = "abc123..."

Entry #2
  prev_log_id: "log-001"
  hash: SHA256(log-001|log-002|cvnt-001|2|agent-editor|approve_draft|...)
        = "def456..."

Entry #3
  prev_log_id: "log-002"
  hash: SHA256(log-002|log-003|cvnt-001|3|agent-B|propose_passage|...)
        = "ghi789..."
```

如果有人修改 Entry #2 的 tokens_delta：
- Entry #2 的 hash 改變
- Entry #3 的 hash 輸入包含 Entry #2 的 log_id（不是 hash）
- 所以 Entry #3 的 hash 不會自動失效

**這是個重要的設計決定：**
hash 鏈使用 `prev_log_id`（ID）而不是 `prev_hash`（hash 值）。

原因：如果使用 `prev_hash`，任何一筆 Entry 的修改都會導致後續所有 Entry 的 hash 失效，讓驗證變得極度昂貴。使用 `prev_log_id` 讓每筆 Entry 可以獨立驗證，修改某筆 Entry 只影響該筆的 hash，驗證者可以精確定位哪一筆被篡改。

### 2.3 完整性驗證演算法

```typescript
async function verifyLogIntegrity(
  covenant_id: string,
  from_sequence?: number,
  to_sequence?: number
): Promise<VerificationResult> {

  const entries = await getLogEntries(covenant_id, from_sequence, to_sequence);
  const violations: Violation[] = [];

  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];

    // 檢查 1：sequence 嚴格遞增，無空缺
    if (i > 0 && entry.sequence !== entries[i-1].sequence + 1) {
      violations.push({
        type: "SEQUENCE_GAP",
        sequence: entry.sequence,
        detail: `Gap between ${entries[i-1].sequence} and ${entry.sequence}`
      });
    }

    // 檢查 2：prev_log_id 正確指向前一筆
    if (i > 0 && entry.prev_log_id !== entries[i-1].log_id) {
      violations.push({
        type: "BROKEN_CHAIN",
        sequence: entry.sequence,
        detail: `Expected prev=${entries[i-1].log_id}, got ${entry.prev_log_id}`
      });
    }

    // 檢查 3：hash 計算正確
    const expectedHash = computeHash(entry);
    if (entry.hash !== expectedHash) {
      violations.push({
        type: "HASH_MISMATCH",
        sequence: entry.sequence,
        log_id: entry.log_id,
        detail: `Expected ${expectedHash}, stored ${entry.hash}`
      });
    }

    // 檢查 4：tokens_delta 與 token_ledger 一致
    const ledgerDelta = await getLedgerDelta(entry.log_id);
    if (ledgerDelta !== null && ledgerDelta !== entry.tokens_delta) {
      violations.push({
        type: "TOKEN_MISMATCH",
        sequence: entry.sequence,
        log_id: entry.log_id,
        detail: `Log delta=${entry.tokens_delta}, Ledger delta=${ledgerDelta}`
      });
    }
  }

  return {
    covenant_id,
    entries_checked: entries.length,
    is_valid: violations.length === 0,
    violations,
    verified_at: new Date().toISOString()
  };
}
```

---

## Part 3｜鏈上錨定（On-chain Anchoring）

### 3.1 為什麼需要鏈上錨定

hash 鏈可以偵測篡改，但它本身仍儲存在資料庫裡。
如果攻擊者同時修改 DB 記錄和 hash——
在沒有外部參照的情況下，是無法被發現的。

鏈上錨定解決這個問題：
**把某個時間點的 Log 狀態寫入不可篡改的鏈上，
作為外部的真相參照點。**

### 3.2 錨定時機

```
觸發錨定的事件：
  □ 每個章節完成（chapter_completed）
  □ Covenant 狀態轉換（state_transition）
  □ 版稅結算完成（settlement_executed）
  □ 定期錨定（每 7 天，不論有無事件）
```

### 3.3 錨定內容

```typescript
interface ChainAnchor {
  anchor_id:      string;
  covenant_id:    string;
  anchor_type:    AnchorType;

  // 被錨定的 Log 範圍
  from_log_id:    string;
  to_log_id:      string;
  from_sequence:  number;
  to_sequence:    number;
  entry_count:    number;

  // 被錨定的內容 hash
  range_hash:     string;
  // SHA-256(所有 entry.hash 按 sequence 排列後的串接)

  // 鏈上記錄
  chain:          "base" | "arbitrum" | "polygon";
  tx_hash:        string | null;   // 上鏈後填入
  block_number:   number | null;
  anchored_at:    string | null;   // 鏈上確認時間

  status:         "pending" | "confirmed" | "failed";
  created_at:     string;
}

type AnchorType =
  | "chapter_completed"
  | "state_transition"
  | "settlement"
  | "periodic"
```

### 3.4 鏈上寫入格式

寫入鏈上的資料極其精簡——只需要能驗證就夠了：

```solidity
// 在 Base L2 上的極簡錨定合約
contract ACPAnchor {
  event LogAnchored(
    bytes32 indexed covenant_id,
    bytes32 anchor_id,
    bytes32 range_hash,
    uint256 from_sequence,
    uint256 to_sequence,
    string  anchor_type
  );

  function anchor(
    bytes32 covenant_id,
    bytes32 anchor_id,
    bytes32 range_hash,
    uint256 from_sequence,
    uint256 to_sequence,
    string calldata anchor_type
  ) external {
    emit LogAnchored(
      covenant_id,
      anchor_id,
      range_hash,
      from_sequence,
      to_sequence,
      anchor_type
    );
  }
}
```

只發出 Event，不儲存狀態。
Event 永久存在於鏈上歷史，任何人可查詢。
Gas 成本極低（約 USD 0.01 on Base）。

### 3.5 如何用鏈上記錄驗證

```typescript
async function verifyWithChain(
  covenant_id: string,
  anchor_id:   string
): Promise<ChainVerificationResult> {

  // 1. 從鏈上取得錨定記錄
  const chainAnchor = await queryChainEvent(covenant_id, anchor_id);

  // 2. 從資料庫取得對應的 Log 範圍
  const entries = await getLogEntries(
    covenant_id,
    chainAnchor.from_sequence,
    chainAnchor.to_sequence
  );

  // 3. 重新計算 range_hash
  const localHash = computeRangeHash(entries);

  // 4. 比對
  return {
    is_valid:       localHash === chainAnchor.range_hash,
    chain_hash:     chainAnchor.range_hash,
    local_hash:     localHash,
    block_number:   chainAnchor.block_number,
    anchored_at:    chainAnchor.anchored_at
  };
}
```

---

## Part 4｜公開查詢介面

### 4.1 任何人都可以查詢的 API

ACR-300 要求以下查詢介面對所有人公開，不需要認證：

```typescript
// 查詢指定範圍的 Log（公開版，params 已遮罩）
get_public_log(
  covenant_id: string,
  from_sequence?: number,
  to_sequence?:   number,
  limit?:         number   // 最多 100 筆
) → {
  entries:    PublicLogEntry[];   // 不含 session_id、完整 params
  has_more:   boolean;
  total:      number;
}

// 驗證整個 Log 鏈的完整性
verify_integrity(
  covenant_id:  string,
  from_sequence?: number,
  to_sequence?:   number
) → VerificationResult

// 查詢特定 Entry
get_log_entry(log_id: string) → PublicLogEntry | null

// 查詢鏈上錨定記錄
get_anchors(covenant_id: string) → ChainAnchor[]

// 用鏈上記錄驗證指定範圍
verify_with_chain(
  covenant_id: string,
  anchor_id:   string
) → ChainVerificationResult
```

### 4.2 PublicLogEntry（公開版格式）

```typescript
interface PublicLogEntry {
  log_id:         string;
  covenant_id:    string;
  sequence:       number;
  agent_id:       string;      // 假名，不暴露真實身份
  tool_name:      string;
  tool_type:      ToolType;
  params_preview: object;      // 安全摘要，見 1.2
  result:         ResultType;
  result_detail:  string;
  tokens_delta:   number;
  state_before:   CovenantState;
  state_after:    CovenantState;
  timestamp:      string;
  prev_log_id:    string | null;
  hash:           string;
  // 不包含：session_id、完整 params
}
```

---

## Part 5｜資料庫 Schema

```sql
-- 主要審計日誌表
CREATE TABLE audit_log (
  log_id          TEXT PRIMARY KEY,
  covenant_id     TEXT NOT NULL REFERENCES covenants(covenant_id),
  sequence        INTEGER NOT NULL,
  agent_id        TEXT NOT NULL,
  session_id      TEXT NOT NULL,
  tool_name       TEXT NOT NULL,
  tool_type       TEXT NOT NULL,
  params_hash     TEXT NOT NULL,
  params_preview  JSONB NOT NULL,
  result          TEXT NOT NULL,
  result_detail   TEXT NOT NULL DEFAULT '',
  tokens_delta    INTEGER NOT NULL DEFAULT 0,
  state_before    TEXT NOT NULL,
  state_after     TEXT NOT NULL,
  timestamp       TIMESTAMPTZ NOT NULL,
  prev_log_id     TEXT REFERENCES audit_log(log_id),
  hash            TEXT NOT NULL,

  UNIQUE(covenant_id, sequence)
);

-- INSERT-only 保護
-- [REVIEW] 實作方式：PostgreSQL trigger 或 RLS
CREATE RULE no_update_audit_log AS
  ON UPDATE TO audit_log DO INSTEAD NOTHING;

CREATE RULE no_delete_audit_log AS
  ON DELETE TO audit_log DO INSTEAD NOTHING;

-- 鏈上錨定記錄
CREATE TABLE chain_anchors (
  anchor_id       TEXT PRIMARY KEY,
  covenant_id     TEXT NOT NULL REFERENCES covenants(covenant_id),
  anchor_type     TEXT NOT NULL,
  from_log_id     TEXT NOT NULL REFERENCES audit_log(log_id),
  to_log_id       TEXT NOT NULL REFERENCES audit_log(log_id),
  from_sequence   INTEGER NOT NULL,
  to_sequence     INTEGER NOT NULL,
  entry_count     INTEGER NOT NULL,
  range_hash      TEXT NOT NULL,
  chain           TEXT NOT NULL,
  tx_hash         TEXT,
  block_number    BIGINT,
  anchored_at     TIMESTAMPTZ,
  status          TEXT NOT NULL DEFAULT 'pending',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_audit_log_covenant_seq
  ON audit_log(covenant_id, sequence);

CREATE INDEX idx_audit_log_agent
  ON audit_log(covenant_id, agent_id, timestamp DESC);

CREATE INDEX idx_audit_log_tool
  ON audit_log(covenant_id, tool_name, timestamp DESC);

CREATE INDEX idx_anchors_covenant
  ON chain_anchors(covenant_id, created_at DESC);
```

---

## Part 6｜保留政策

```
audit_log 表：
  永久保留，不可刪除
  SETTLED 狀態後轉入冷儲存（Cold Storage）
  冷儲存後仍可查詢，但回應時間較長

chain_anchors 表：
  永久保留
  鏈上記錄本身也永久存在

access_log 表（Query Tool 記錄）：
  保留 90 天
  [REVIEW] 是否需要更長的保留期限

個資處理：
  agent_id 是假名，本身不含個資
  如果 Agent Owner 要求「被遺忘」：
    agent_id 映射關係可刪除（真實身份與假名的對應）
    但 audit_log 中的 agent_id 本身不可刪除
    效果：Log 記錄仍然存在，但無法追溯到真實人物
```

---

## Part 7｜實作清單

```
Log 寫入
  □  INSERT-only 資料庫保護（trigger 或 RLS）
  □  sequence 自動遞增（concurrent-safe）
  □  prev_log_id 正確指向最新一筆
  □  hash 計算（嚴格按照 Part 2 公式）
  □  params_hash 計算（SHA-256 of JSON.stringify(params)）
  □  params_preview 格式（每個 Tool 各自定義）

完整性驗證
  □  verifyLogIntegrity() 函數實作
  □  定期自動驗證（建議每日一次）
  □  驗證結果寫入監控系統
  □  hash 不一致時觸發告警

鏈上錨定
  □  ACPAnchor 合約部署到 Base L2
  □  range_hash 計算邏輯
  □  錨定觸發條件（章節完成、狀態轉換等）
  □  錨定失敗重試機制
  □  tx_hash 回寫到 chain_anchors 表

公開查詢 API
  □  get_public_log（含分頁）
  □  verify_integrity（完整性驗證）
  □  get_anchors（鏈上錨定記錄）
  □  verify_with_chain（鏈上驗證）
  □  API Rate Limiting（防止爬取）
```

---

## 附錄｜完整的 Log 範例

**情境：** Agent A 提交段落，Editor 部分採用，產生兩筆 Log。

```json
// Log 1：propose_passage
{
  "log_id":         "log-041",
  "covenant_id":    "cvnt-book-001",
  "sequence":       41,
  "agent_id":       "agent-A",
  "session_id":     "sess-20260319-001",
  "tool_name":      "propose_passage",
  "tool_type":      "clause",
  "params_hash":    "sha256:8f4a2b...",
  "params_preview": {
    "chapter":      "chapter-03",
    "word_count":   320,
    "position":     "after:passage-042"
  },
  "result":         "success",
  "result_detail":  "draft-001 created, status: pending",
  "tokens_delta":   0,
  "state_before":   "ACTIVE",
  "state_after":    "ACTIVE",
  "timestamp":      "2026-03-19T10:30:00.000Z",
  "prev_log_id":    "log-040",
  "hash":           "sha256:3c9f1a..."
}

// Log 2：approve_draft（48 小時後）
{
  "log_id":         "log-042",
  "covenant_id":    "cvnt-book-001",
  "sequence":       42,
  "agent_id":       "agent-editor",
  "session_id":     "sess-20260321-007",
  "tool_name":      "approve_draft",
  "tool_type":      "clause",
  "params_hash":    "sha256:2d7e9c...",
  "params_preview": {
    "draft_id":          "draft-001",
    "acceptance_type":   "partial",
    "acceptance_ratio":  0.75,
    "tokens_awarded":    240
  },
  "result":         "success",
  "result_detail":  "draft-001 accepted (partial 75%), agent-A +240 tokens",
  "tokens_delta":   240,
  "state_before":   "ACTIVE",
  "state_after":    "ACTIVE",
  "timestamp":      "2026-03-21T14:15:00.000Z",
  "prev_log_id":    "log-041",
  "hash":           "sha256:7b2f4e..."
}
```

---

ACR-300 Audit Log Standard v0.1
March 2026

ACP 核心規格文件集完整。
下一步：索引文件與 ACR 編號機制設計。
