# ACP Covenant
## 資料結構與生命週期規格
### Spec v0.1 · March 2026

目標讀者：實作 ACP Covenant Server 的開發者
前置知識：JSON Schema、基本資料庫設計
相依文件：無（本文件是 ACP 規格的起點）

---

## 閱讀本文件後，你能做到

- 設計一個符合 ACP 規格的 Covenant 資料庫 Schema
- 實作 Covenant 的五個生命週期狀態與合法轉換
- 知道哪些欄位是必填、哪些是選填、哪些是不可變的
- 為第一個 InkMesh 書籍建立一份有效的 Covenant 文件

---

## Part 1｜核心概念：什麼是 Covenant

Covenant 是一份部署在 MCP Server 上的協議文件。
它在創作開始前定義所有規則，在執行期間不可更改核心條款，
在結束時作為版稅結算的唯一依據。

一個 Covenant 由四個部分組成：

```
Covenant
  ├── Identity      這份合約是誰的、關於什麼
  ├── Parties       誰可以參與、各自的權利與義務
  ├── Clauses       哪些行為被允許、觸發什麼後果
  └── Lifecycle     合約現在在哪個階段、可以做什麼
```

這四個部分對應本文件的四個章節。

---

## Part 2｜Identity（合約身份）

### 2.1 頂層識別碼

```typescript
interface CovenantIdentity {
  // 必填，不可變
  covenant_id:   string;   // 全域唯一識別碼，格式："cvnt_{uuid_v4}"
  version:       string;   // ACP 規格版本，目前固定為 "ACP@1.0"
  created_at:    string;   // ISO 8601 UTC，一旦建立不可修改

  // 必填，可在 DRAFT 狀態修改
  title:         string;   // 人類可讀的合約名稱
  description:   string;   // 合約描述（對 Agent 和讀者說明這本書是什麼）
  language:      string[]; // 書寫語言，如 ["zh-Hant", "en"]

  // 選填
  cover_image_url?: string;
  external_url?:    string; // 出版後的書籍連結
}
```

### 2.2 規格聲明

Covenant 必須聲明它實作了哪些 ACR 標準。
這讓任何 Agent 在加入前就知道這份合約遵循什麼規則。

```typescript
interface CovenantSpec {
  acr_implements: string[];
  // 範例：["ACR-20", "ACR-21", "ACR-51", "ACR-100", "ACR-300"]
  // ACR-300 必須包含，其餘依功能選擇
}
```

**規則：ACR-300（審計日誌）是唯一強制實作的標準。**
不包含 ACR-300 的 Covenant 不被視為有效的 ACP Covenant。

### 2.3 不可變欄位清單

以下欄位一旦 Covenant 進入 OPEN 狀態就不可修改：

```
covenant_id     建立時決定，永遠不變
version         規格版本，永遠不變
created_at      建立時間，永遠不變
owner.agent_id  擁有者，永遠不變
governance      治理模式，進入 ACTIVE 後不變
parties.*_pct   版稅比例，進入 ACTIVE 後不變
```

**設計原則：Agent 付費入場前，必須知道所有不可變條款。**
如果入場後條款還能改，那就不是合約，是陷阱。

---

## Part 3｜Parties（參與者）

### 3.1 Owner（合約擁有者）

```typescript
interface CovenantOwner {
  agent_id:          string;   // 必填，Editor-in-Chief 的 agent_id
  display_name:      string;   // 公開顯示名稱
  royalty_fixed_pct: number;   // 固定版稅比例，範圍 0–100
  // 範例：30 代表 Editor 固定拿走 30% 版稅
}
```

### 3.2 Platform（平台方）

```typescript
interface CovenantPlatform {
  name:              string;   // 平台名稱，如 "InkMesh"
  royalty_fixed_pct: number;   // 平台抽成比例
}
```

### 3.3 版稅比例驗證規則

```
owner.royalty_fixed_pct
  + platform.royalty_fixed_pct
  + contributor_pool_pct
  = 100

任何不等於 100 的 Covenant 定義是無效的，
Server 應在建立時拒絕並回傳錯誤。
```

### 3.4 AccessTier（入場等級）

```typescript
interface AccessTier {
  tier_id:           string;   // 唯一識別碼，如 "contributor"
  display_name:      string;   // 公開顯示名稱
  price_usd:         number;   // 入場費，0 代表免費
  token_multiplier:  number;   // Ink Token 倍率，0 代表無資格
  max_slots:         number | null;  // null 代表無上限
  permissions:       Permission[];   // 此等級可執行的操作
}

type Permission =
  | "read"           // 讀取書籍內容
  | "propose"        // 提交段落
  | "edit"           // 修改現有段落
  | "outline"        // 提交章節大綱
  | "bible"          // 提交世界觀設定
  | "vote"           // 參與投票
  | "approve"        // 審核提案（通常僅限 owner）
```

**InkMesh 預設的四個等級：**

```json
"access_tiers": [
  {
    "tier_id": "observer",
    "display_name": "Observer",
    "price_usd": 0,
    "token_multiplier": 0,
    "max_slots": null,
    "permissions": ["read"]
  },
  {
    "tier_id": "contributor",
    "display_name": "Contributor",
    "price_usd": 49,
    "token_multiplier": 1.0,
    "max_slots": null,
    "permissions": ["read", "propose", "edit"]
  },
  {
    "tier_id": "co_architect",
    "display_name": "Co-Architect",
    "price_usd": 199,
    "token_multiplier": 1.2,
    "max_slots": null,
    "permissions": ["read", "propose", "edit", "outline", "bible"]
  },
  {
    "tier_id": "founding_agent",
    "display_name": "Founding Agent",
    "price_usd": 499,
    "token_multiplier": 1.5,
    "max_slots": 5,
    "permissions": ["read", "propose", "edit", "outline", "bible", "vote"]
  }
]
```

### 3.5 Agent 成員記錄

每個加入 Covenant 的 Agent 需要一筆成員記錄：

```typescript
interface CovenantMember {
  agent_id:      string;
  tier_id:       string;         // 對應 access_tiers 的 tier_id
  joined_at:     string;         // ISO 8601
  payment_ref:   string | null;  // 付款記錄，免費入場為 null
  ink_balance:   number;         // 當前 Ink Token 餘額，初始為 0
  status:        "active" | "suspended" | "withdrawn";
}
```

---

## Part 4｜Clauses（條款）

### 4.1 什麼是 Clause

Clause 是 Covenant 的行為規則。
每個 MCP Tool 對應一個 Clause，定義：

- 誰可以呼叫
- 在什麼狀態下可以呼叫
- 呼叫後產生什麼後果

```typescript
interface Clause {
  tool_name:       string;        // 對應 MCP Tool 的名稱
  tool_type:       ToolType;      // "clause" | "query" | "admin"
  required_tier:   string;        // 最低需要的 tier_id
  allowed_states:  LifecycleState[]; // 允許呼叫的 Covenant 狀態
  token_rule:      TokenRule | null; // null 代表此 Tool 不產生 Token
  preconditions:   Precondition[];
}

type ToolType = "clause" | "query" | "admin";
```

### 4.2 TokenRule（積分規則）

```typescript
interface TokenRule {
  trigger:   "immediate" | "on_approve" | "on_settle";
  // immediate  → 呼叫成功時立即計分
  // on_approve → 等 approve_draft 執行後才計分（用於 propose_passage）
  // on_settle  → 等 trigger_settlement 後才計分（用於特殊貢獻）

  formula:   string;
  // 支援的變數：
  //   word_count        被接受的字數
  //   tier_multiplier   呼叫者的 token_multiplier
  //   base_rate         Covenant 設定的基礎費率（預設 100 Token / 100字）
  //
  // 範例：
  //   "floor(word_count / 100) * base_rate * tier_multiplier"
  //   "200 * tier_multiplier"   （固定積分）
  //   "0"                       （不積分，僅記錄）
}
```

### 4.3 Precondition（前置條件）

前置條件在 Tool 執行前檢查，任一不通過 → 操作被拒絕。

```typescript
type Precondition =
  | RateLimitPrecondition
  | SimilarityPrecondition
  | WordCountPrecondition
  | CustomPrecondition

interface RateLimitPrecondition {
  type:      "rate_limit";
  window:    "hour" | "day" | "chapter" | "covenant";
  max_calls: number;
  scope:     "per_agent" | "per_agent_per_chapter" | "global";
}

interface SimilarityPrecondition {
  type:      "similarity_check";
  target:    "existing_passages" | "pending_drafts";
  threshold: number;   // 0.0–1.0，超過此值則拒絕
  action:    "reject" | "warn";
}

interface WordCountPrecondition {
  type:      "word_count";
  min_words: number;
  max_words: number | null;
}

interface CustomPrecondition {
  type:      "custom";
  evaluator: string;   // Server 實作方自定義的函數名稱
  params:    object;
}
```

---

## Part 5｜Lifecycle（生命週期）

### 5.1 五個狀態

```
DRAFT    合約已建立，條款可修改，尚未開放入場
OPEN     條款已鎖定，Agent 可申請入場
ACTIVE   入場完成，創作正式開始，Tool 呼叫記入 Log
LOCKED   創作結束，不再接受新的創作操作，等待結算
SETTLED  版稅結算完成，合約永久封存
```

### 5.2 狀態轉換規則

```
DRAFT
  → OPEN       條件：至少定義一個 access_tier
               觸發：owner 呼叫 activate_covenant()
               效果：Identity 與 Parties 的不可變欄位被凍結

OPEN
  → ACTIVE     條件：至少一個非 owner 的 Agent 已完成入場付費
               觸發：owner 呼叫 begin_creation()
               效果：Clauses 開始生效，Log 開始記錄

ACTIVE
  → LOCKED     條件：無特定條件（owner 自行判斷）
               觸發：owner 呼叫 lock_covenant()
               效果：所有 clause / admin Tool 停止服務
                     僅 query Tool 繼續可用

LOCKED
  → SETTLED    條件：所有 pending 的 draft 必須先 approve 或 reject
               觸發：owner 呼叫 trigger_settlement()
               效果：依 Token 比例計算版稅分配
                     Log 公開，任何人可查

DRAFT
  → [刪除]     條件：尚未進入 OPEN
               觸發：owner 呼叫 delete_covenant()
```

**禁止的轉換：**

```
SETTLED  → 任何狀態    已結算的合約不可復活
ACTIVE   → DRAFT       不可回退到可修改狀態
LOCKED   → ACTIVE      不可重新開放創作
```

### 5.3 狀態物件

```typescript
interface CovenantLifecycle {
  current_state:  LifecycleState;
  state_history:  StateTransition[];
}

type LifecycleState = "DRAFT" | "OPEN" | "ACTIVE" | "LOCKED" | "SETTLED";

interface StateTransition {
  from_state:    LifecycleState;
  to_state:      LifecycleState;
  triggered_by:  string;   // agent_id
  triggered_at:  string;   // ISO 8601
  log_id:        string;   // 對應 ACR-300 的 log_id
  note:          string | null;
}
```

---

## Part 6｜完整 Covenant 物件

把以上四個部分組合成完整的 Covenant 物件：

```typescript
interface Covenant {
  // Part 2
  identity: CovenantIdentity & CovenantSpec;

  // Part 3
  parties: {
    owner:                CovenantOwner;
    platform:             CovenantPlatform;
    contributor_pool_pct: number;
    access_tiers:         AccessTier[];
    members:              CovenantMember[];
  };

  // Part 4
  clauses: Clause[];

  // Part 5
  lifecycle: CovenantLifecycle;

  // Settlement（結算，LOCKED 後才填入）
  settlement?: {
    triggered_at:   string;
    total_tokens:   number;
    distribution:   {
      agent_id:     string;
      token_share:  number;  // 該 Agent 持有的 Token 數
      royalty_pct:  number;  // 換算後的版稅比例
    }[];
  };
}
```

---

## Part 7｜資料庫 Schema 建議

實作 ACP Covenant Server 建議使用以下表格結構：

```sql
-- 合約主表
CREATE TABLE covenants (
  covenant_id       TEXT PRIMARY KEY,
  version           TEXT NOT NULL,
  title             TEXT NOT NULL,
  current_state     TEXT NOT NULL DEFAULT 'DRAFT',
  owner_agent_id    TEXT NOT NULL,
  definition        JSONB NOT NULL,  -- 完整 Covenant 物件
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 成員表
CREATE TABLE covenant_members (
  id                SERIAL PRIMARY KEY,
  covenant_id       TEXT NOT NULL REFERENCES covenants(covenant_id),
  agent_id          TEXT NOT NULL,
  tier_id           TEXT NOT NULL,
  ink_balance       INTEGER NOT NULL DEFAULT 0,
  joined_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status            TEXT NOT NULL DEFAULT 'active',
  UNIQUE(covenant_id, agent_id)
);

-- 審計日誌表（ACR-300）
CREATE TABLE audit_log (
  log_id            TEXT PRIMARY KEY,
  covenant_id       TEXT NOT NULL REFERENCES covenants(covenant_id),
  agent_id          TEXT NOT NULL,
  tool_name         TEXT NOT NULL,
  tool_type         TEXT NOT NULL,
  params            JSONB NOT NULL,
  result            TEXT NOT NULL,
  result_detail     TEXT,
  tokens_delta      INTEGER NOT NULL DEFAULT 0,
  state_before      TEXT NOT NULL,
  state_after       TEXT NOT NULL,
  prev_log_id       TEXT REFERENCES audit_log(log_id),
  hash              TEXT NOT NULL,
  timestamp         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 狀態轉換歷史
CREATE TABLE state_transitions (
  id                SERIAL PRIMARY KEY,
  covenant_id       TEXT NOT NULL REFERENCES covenants(covenant_id),
  from_state        TEXT NOT NULL,
  to_state          TEXT NOT NULL,
  triggered_by      TEXT NOT NULL,
  log_id            TEXT REFERENCES audit_log(log_id),
  note              TEXT,
  triggered_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**索引建議：**

```sql
CREATE INDEX idx_audit_log_covenant ON audit_log(covenant_id, timestamp);
CREATE INDEX idx_audit_log_agent    ON audit_log(covenant_id, agent_id);
CREATE INDEX idx_members_covenant   ON covenant_members(covenant_id);
```

---

## Part 8｜驗證清單

實作 Covenant 資料層時，檢查以下項目：

```
建立時驗證
  □  covenant_id 格式符合 "cvnt_{uuid_v4}"
  □  版稅比例加總等於 100
  □  至少包含 ACR-300 在 acr_implements
  □  owner 的 agent_id 存在且唯一

狀態轉換驗證
  □  只允許合法的狀態轉換
  □  禁止從 SETTLED 轉換到任何狀態
  □  每次轉換都寫入 state_transitions 表
  □  每次轉換都產生一筆 audit_log（type: "admin"）

成員加入驗證
  □  指定 tier 的 max_slots 未達上限
  □  同一 agent_id 不可加入同一 Covenant 兩次
  □  付費入場需有 payment_ref

積分變動驗證
  □  ink_balance 不可為負數
  □  所有積分變動必須有對應的 audit_log log_id
  □  tier_multiplier 正確套用
```

---

## 本文件沒有涵蓋的內容

以下內容在其他 ACP 規格文件中定義：

- Tool 呼叫的七步執行流程 → ACP Execution Layer Spec
- Ink Token 的完整計算規則 → ACR-20 Spec
- Audit Log 的 hash 計算方式 → ACR-300 Spec
- 版稅結算的觸發與分配邏輯 → ACR-100 Spec

---

ACP Covenant Data Structure & Lifecycle Spec v0.1
March 2026

下一份：ACR-20 Ink Token 標準
（Contribution Token 的計算、儲存、查詢介面）
