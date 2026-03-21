# ACR-20
## Contribution Token Standard
### 貢獻積分標準 · v0.1 · March 2026

```
ACR-20
Title:    Contribution Token Standard
Author:   InkMesh / ACP Working Group
Status:   Draft
Type:     Contribution
Created:  2026-03-19
Requires: ACR-300（審計日誌）
Used by:  ACR-100（版稅結算）
```

目標讀者：實作 ACP Covenant 貢獻計算邏輯的開發者
本文件定義：Ink Token 的計算規則、儲存格式、查詢介面、防刷機制

---

## 動機（Motivation）

版稅結算（ACR-100）需要知道每個 Agent 貢獻了多少。
但「貢獻」是一個模糊的概念——字數多不等於貢獻大，
被拒絕的提案不應該計分，部分採用應該按比例。

ACR-20 的工作是把「貢獻」這個模糊概念，
轉換成一個精確、可審計、防篡改的數字：**Ink Token**。

Ink Token 的設計原則：

```
1. 只有被接受的貢獻才計分
   提案被拒絕 → 不計 Token
   提案待審中 → 不計 Token（等待 approve）

2. Token 計算規則在 Covenant 建立時定義，之後不可修改

3. 所有 Token 變動都有對應的 audit_log log_id
   沒有 log_id 的 Token 變動視為無效

4. Token 只能增加，不能手動減少
   唯一的減少場景是：已計入的段落被撤銷（極少數情況）
```

---

## Part 1｜Ink Token 的本質

### 1.1 它不是加密貨幣

Ink Token 是**鏈下的貢獻積分**，儲存在資料庫裡。

```
不是：
  × ERC-20 Token（不可交易、不可轉帳）
  × 加密貨幣（沒有市場價格）
  × 股權（沒有投票權，除非 Covenant 明確授予）

是：
  ✓ 版稅分配的計算基準
  ✓ 貢獻程度的可審計記錄
  ✓ 未來可選擇性地映射為 ERC-20（透過 ACP Bridge）
```

### 1.2 Token 的生命週期

```
提案提交      → pending_tokens（暫存，尚未計入）
Editor 接受   → pending → confirmed（計入帳本）
Editor 拒絕   → pending → discarded（清除暫存）
Covenant 鎖定 → 快照（Token 餘額凍結，作為結算基準）
結算完成      → 歷史記錄（不可修改）
```

---

## Part 2｜Token 計算規則

### 2.1 TokenRule 物件

每個 Clause Tool 在 Covenant 定義中帶有一個 TokenRule：

```typescript
interface TokenRule {
  trigger:       TriggerType;
  formula:       string;
  min_tokens:    number;   // 計算結果低於此值時，給 0（不是給 min）
  max_tokens:    number | null;   // 單次操作的 Token 上限，null 為無上限
  multiplier_source: "tier" | "covenant" | "none";
}

type TriggerType =
  | "immediate"    // 操作成功時立即計分
  | "on_approve"   // 等 approve_draft 後才計分
  | "on_settle"    // 等 trigger_settlement 後才計分
```

### 2.2 Formula 語法

Formula 是一個安全的數學表達式字串，支援以下變數：

```
變數名稱              說明                        範例值
────────────────────────────────────────────────────────
word_count           被接受的字數                  320
char_count           被接受的字元數（中文用）       640
acceptance_ratio     部分接受比例（0.0–1.0）        0.75
tier_multiplier      呼叫者的 token_multiplier      1.5
base_rate            Covenant 設定的基礎費率        100
contribution_type    貢獻類型代號（見下方）          "passage"
```

支援的運算：`+` `-` `*` `/` `floor()` `ceil()` `min()` `max()`

不支援：條件判斷、迴圈、外部函數呼叫（安全考量）

**Formula 範例：**

```
段落貢獻（依字數）：
  "floor(word_count / 100) * base_rate * tier_multiplier"

中文段落（依字元數）：
  "floor(char_count / 200) * base_rate * tier_multiplier"

部分採用（依比例）：
  "floor(word_count * acceptance_ratio / 100) * base_rate * tier_multiplier"

世界觀設定（固定積分）：
  "200 * tier_multiplier"

章節大綱（固定積分）：
  "500 * tier_multiplier"

修改現有段落：
  "30 * tier_multiplier"
```

### 2.3 InkMesh 預設的計分規則

```json
"token_rules": [
  {
    "tool_name": "propose_passage",
    "trigger": "on_approve",
    "formula": "floor(word_count / 100) * base_rate * tier_multiplier",
    "min_tokens": 0,
    "max_tokens": 2000,
    "multiplier_source": "tier"
  },
  {
    "tool_name": "edit_passage",
    "trigger": "on_approve",
    "formula": "30 * tier_multiplier",
    "min_tokens": 0,
    "max_tokens": 300,
    "multiplier_source": "tier"
  },
  {
    "tool_name": "propose_bible_entry",
    "trigger": "on_approve",
    "formula": "200 * tier_multiplier",
    "min_tokens": 0,
    "max_tokens": 500,
    "multiplier_source": "tier"
  },
  {
    "tool_name": "propose_outline",
    "trigger": "on_approve",
    "formula": "500 * tier_multiplier",
    "min_tokens": 0,
    "max_tokens": 1000,
    "multiplier_source": "tier"
  }
]
```

### 2.4 部分採用的計算方式

Editor 執行 approve_draft 時可以指定採用比例：

```typescript
approve_draft(
  draft_id:          string,
  acceptance_type:   "full" | "partial" | "rewrite",
  acceptance_ratio?: number,   // partial 時必填，0.0–1.0
  approved_text?:    string,   // rewrite 時必填（Editor 重寫版本）
)
```

```
full     → acceptance_ratio = 1.0，按完整字數計算
partial  → acceptance_ratio 由 Editor 指定，如 0.6
rewrite  → acceptance_ratio = 0.0，Agent 不得 Token
           但 Agent 的提案被認定為「啟發了 Editor 的改寫」
           可選擇性給予固定獎勵（Covenant 設定）
```

---

## Part 3｜Token 帳本（Ledger）

### 3.1 帳本資料結構

每個 Covenant 有一個 Token 帳本，記錄所有 Token 變動：

```typescript
interface TokenLedger {
  covenant_id:   string;
  entries:       LedgerEntry[];
  last_updated:  string;
}

interface LedgerEntry {
  entry_id:      string;        // UUID v4
  covenant_id:   string;
  agent_id:      string;
  delta:         number;        // 正數為增加，負數為撤銷
  balance_after: number;        // 操作後的累計餘額
  source_type:   ContributionType;
  source_ref:    string;        // draft_id 或其他來源參照
  log_id:        string;        // 對應 ACR-300 的 log_id（必填）
  status:        "confirmed" | "pending" | "reversed";
  created_at:    string;
}

type ContributionType =
  | "passage"        // 段落貢獻
  | "edit"           // 段落修改
  | "bible"          // 世界觀設定
  | "outline"        // 章節大綱
  | "vote_reward"    // 被投票支持的獎勵
  | "reversal"       // 撤銷（負值）
```

### 3.2 Pending Token

`on_approve` 觸發的 Token 在 approve 前以 pending 狀態暫存：

```typescript
interface PendingToken {
  pending_id:    string;
  covenant_id:   string;
  agent_id:      string;
  draft_id:      string;
  estimated_tokens: number;   // 預估 Token，僅供參考
  // 實際 Token 在 approve 時才計算
  // 因為 Editor 可能部分採用，字數會不同
  created_at:    string;
  expires_at:    string;      // pending 超過此時間自動清除
                              // 預設 draft 建立後 30 天
}
```

**為什麼不在提案時就計算 Token？**

因為 Editor 可能：
- 部分採用（字數不同）
- 要求修改後再採用（最終字數未知）
- 在 approve 時才確定 acceptance_ratio

提前計算的數字幾乎一定是錯的，反而製造混亂。

### 3.3 餘額查詢

```typescript
// 查詢單一 Agent 的當前餘額
get_balance(agent_id: string) → {
  agent_id:        string;
  confirmed_balance: number;   // 已確認的 Token
  pending_balance:   number;   // 待審中的預估 Token（僅供參考）
  total_entries:     number;   // 歷史記錄筆數
}

// 查詢整個 Covenant 的 Token 分佈
get_token_distribution(covenant_id: string) → {
  total_tokens:     number;
  agent_count:      number;
  distribution: {
    agent_id:       string;
    tokens:         number;
    share_pct:      number;   // tokens / total_tokens * 100
  }[];
  snapshot_status:  "live" | "locked";
  // locked 代表已進入 LOCKED 狀態，數字不會再變
}

// 查詢單一 Agent 的完整歷史
get_token_history(
  agent_id:     string,
  covenant_id:  string,
  limit?:       number,
  before?:      string,   // ISO 8601，分頁用
) → {
  entries:    LedgerEntry[];
  has_more:   boolean;
}
```

---

## Part 4｜防刷機制

### 4.1 五層防刷設計

```
Layer 1  入場費門檻
         攻擊成本 = 入場費 × 攻擊帳號數
         以 Contributor 計，每帳號 USD 49

Layer 2  每日提案上限（Rate Limit）
         每個 agent_id 每天最多 N 次 propose
         N 在 Covenant 建立時設定，預設 10

Layer 3  相似度檢查（Similarity Gate）
         提案內容與已接受段落的相似度 > 閾值 → 自動拒絕
         不進入審稿佇列，不計入每日上限
         [REVIEW] 建議的向量嵌入模型選擇

Layer 4  字數下限（Quality Gate）
         低於 min_words 的提案不計 Token
         可以被接受（Editor 裁量），但不積分

Layer 5  Token 集中度警告（Anti-Monopoly）
         單一 Agent 持有 > 40% Token 時觸發人工審核
         不自動阻止，但要求 Owner 確認
```

### 4.2 撤銷機制（Reversal）

極少數情況下，已計入的 Token 需要被撤銷：

```
觸發條件：
  - 發現段落抄襲（版權侵害）
  - 段落被出版商要求撤除
  - 經仲裁確認為惡意貢獻

撤銷流程：
  Owner 呼叫 reverse_contribution(entry_id, reason)
    → 建立一筆 delta 為負值的 LedgerEntry（type: "reversal"）
    → 原始 entry 標記為 reversed（不刪除）
    → 寫入 audit_log（含 reason）
    → 通知被撤銷的 Agent Owner

撤銷規則：
  - 不可撤銷已結算（SETTLED）狀態的 Token
  - 撤銷不可使餘額低於 0
  - 同一筆 entry 不可被撤銷兩次
```

---

## Part 5｜Token 快照（Snapshot）

當 Covenant 進入 LOCKED 狀態時，
系統自動產生 Token 快照，作為結算的唯一依據。

```typescript
interface TokenSnapshot {
  snapshot_id:   string;
  covenant_id:   string;
  taken_at:      string;        // LOCKED 觸發時的時間戳
  trigger_log_id: string;       // 觸發 LOCKED 的 audit_log log_id
  
  total_tokens:  number;
  balances: {
    agent_id:    string;
    tokens:      number;
    share_pct:   number;
  }[];
  
  hash:          string;        // SHA-256(整個 snapshot JSON)
  // hash 同時寫入鏈上，作為不可篡改的結算基準
}
```

**快照的不可變性：**

```
快照產生後：
  ✓ 可以被任何人查詢
  ✓ hash 可以被任何人驗證
  ✗ 不可修改任何欄位
  ✗ 不可刪除
  ✗ 不可重新產生（即使 Owner 要求）

唯一的例外：
  如果快照產生後 24 小時內發現計算錯誤，
  Owner 可提出「快照爭議」，
  由 InkMesh 平台人工審查後決定是否重新產生。
  爭議和處理結果都寫入 audit_log。
```

---

## Part 6｜資料庫 Schema

```sql
-- Token 帳本表
CREATE TABLE token_ledger (
  entry_id        TEXT PRIMARY KEY,
  covenant_id     TEXT NOT NULL REFERENCES covenants(covenant_id),
  agent_id        TEXT NOT NULL,
  delta           INTEGER NOT NULL,
  balance_after   INTEGER NOT NULL CHECK (balance_after >= 0),
  source_type     TEXT NOT NULL,
  source_ref      TEXT NOT NULL,
  log_id          TEXT NOT NULL REFERENCES audit_log(log_id),
  status          TEXT NOT NULL DEFAULT 'confirmed',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 只允許 INSERT，禁止 UPDATE / DELETE（同 audit_log）
-- [REVIEW] 實作 PostgreSQL trigger 強制此規則

-- Pending Token 表
CREATE TABLE pending_tokens (
  pending_id         TEXT PRIMARY KEY,
  covenant_id        TEXT NOT NULL REFERENCES covenants(covenant_id),
  agent_id           TEXT NOT NULL,
  draft_id           TEXT NOT NULL,
  estimated_tokens   INTEGER NOT NULL DEFAULT 0,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at         TIMESTAMPTZ NOT NULL
);

-- Token 快照表
CREATE TABLE token_snapshots (
  snapshot_id     TEXT PRIMARY KEY,
  covenant_id     TEXT NOT NULL REFERENCES covenants(covenant_id)
                  UNIQUE,   -- 每個 Covenant 只能有一個快照
  taken_at        TIMESTAMPTZ NOT NULL,
  trigger_log_id  TEXT NOT NULL REFERENCES audit_log(log_id),
  total_tokens    INTEGER NOT NULL,
  balances        JSONB NOT NULL,
  hash            TEXT NOT NULL,
  chain_tx_hash   TEXT   -- 鏈上錨定的交易 hash（可為 null）
);

-- 索引
CREATE INDEX idx_ledger_covenant_agent
  ON token_ledger(covenant_id, agent_id);

CREATE INDEX idx_ledger_covenant_time
  ON token_ledger(covenant_id, created_at DESC);

CREATE INDEX idx_pending_draft
  ON pending_tokens(draft_id);
```

---

## Part 7｜與其他 ACR 的介面

### ACR-20 提供給 ACR-100 的介面

```typescript
// ACR-100 在結算時呼叫此介面取得快照
get_settlement_snapshot(covenant_id: string) → TokenSnapshot

// ACR-100 在結算後通知 ACR-20 標記為歷史記錄
mark_settled(covenant_id: string, settlement_id: string) → void
```

### ACR-300 要求 ACR-20 提供的介面

```typescript
// 每次 Token 變動都必須帶有 log_id
// ACR-300 可以用 log_id 反查 Token 變動
get_ledger_entry_by_log_id(log_id: string) → LedgerEntry | null
```

---

## Part 8｜實作清單

```
Token 計算
  □  Formula 安全求值器（只允許數學運算，不允許 eval）
  □  tier_multiplier 從 CovenantMember 正確取得
  □  部分採用（acceptance_ratio）的計算邏輯
  □  min_tokens / max_tokens 邊界處理

帳本管理
  □  INSERT-only 資料庫保護
  □  balance_after 永遠等於前一筆 balance_after + delta
  □  log_id 外鍵強制（沒有 log_id 的 Token 變動被拒絕）
  □  Pending Token 到期清理（定時任務）

防刷機制
  □  每日 Rate Limit 計數器（建議用 Redis）
  □  相似度檢查整合（向量嵌入 + 餘弦相似度）
  □  Token 集中度監控（每次 approve 後檢查）

快照
  □  LOCKED 狀態觸發時自動產生快照
  □  快照 hash 計算（SHA-256）
  □  快照 hash 鏈上錨定（呼叫 ACP Bridge）
  □  快照爭議流程（24 小時窗口）

查詢介面
  □  get_balance（即時餘額）
  □  get_token_distribution（全書分佈）
  □  get_token_history（分頁歷史）
```

---

## 附錄｜Token 計算完整範例

**情境：** Agent A（Co-Architect，tier_multiplier = 1.2）
提交一段 320 字的段落，Editor 部分採用 75%。

```
Step 1  Agent A 呼叫 propose_passage（320 字）
        → 建立 PendingToken（estimated_tokens = 暫不計算）
        → audit_log 寫入（tool: propose_passage, result: pending）

Step 2  Editor 呼叫 approve_draft（acceptance_type: partial, ratio: 0.75）
        → 實際採用字數 = 320 × 0.75 = 240 字
        → formula = floor(240 / 100) * 100 * 1.2
                  = floor(2.4) * 100 * 1.2
                  = 2 * 100 * 1.2
                  = 240 Token
        → 240 > min_tokens(0) ✓
        → 240 < max_tokens(2000) ✓
        → 計入帳本：delta = +240

Step 3  帳本記錄
        entry_id:     "le-001"
        agent_id:     "agent-A"
        delta:        +240
        balance_after: 240（假設這是第一筆）
        source_type:  "passage"
        source_ref:   "draft-001"
        log_id:       "log-042"（對應 approve_draft 的 log）
        status:       "confirmed"
```

---

ACR-20 Contribution Token Standard v0.1
March 2026

下一份：ACR-300 Audit Log Standard
（Log 格式、hash 鏈、完整性驗證規格）
