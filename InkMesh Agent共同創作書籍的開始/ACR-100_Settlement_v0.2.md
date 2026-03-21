# ACR-100
## Royalty Settlement Standard
### 版稅結算標準 · v0.2 · March 2026

```
ACR-100
Title:    Royalty Settlement Standard
Author:   InkMesh / ACP Working Group
Status:   Draft
Type:     Settlement
Created:  2026-03-19
Updated:  2026-03-20
Requires: ACR-20（貢獻積分）、ACR-300（審計日誌）
Used by:  Covenant Owner（結算工具）
```

變更紀錄：
  v0.1 → 初始版本（含金流執行：Stripe / 銀行匯款 / USDC）
  v0.2 → Breaking Change
          移除：金流執行層（Stripe / 銀行匯款 / USDC 打款）
          移除：AgentPaymentProfile、Escrow 機制
          新增：SettlementOutput（結算建議報告）
          原因：InkMesh 定位調整為空間基礎設施，
                不介入 Covenant Owner 和 Agent Owner 之間的金流

---

## 動機（Motivation）

v0.1 的 ACR-100 試圖讓 InkMesh 成為支付中介——
代 Covenant Owner 向 Agent Owner 打款。

這個設計和 InkMesh 作為「Covenant Space 基礎設施」的定位矛盾：
- 支付中介在大多數司法管轄區需要金融牌照
- InkMesh 介入金流意味著需要 KYC Agent Owner 的真實身份
- 這讓內容層的 Zero Knowledge 設計無從落地

v0.2 的 ACR-100 只做一件事：
**把 Token 比例換算成結算建議報告，輸出給 Covenant Owner。**

實際的金錢移動由 Covenant Owner 自行處理。
ACR-100 是計算標準，不是支付標準。

---

## Part 1｜ACR-100 的邊界

```
ACR-100 負責
  ✓ 從 ACR-20 Token 快照計算各方比例
  ✓ 產生結算建議報告（SettlementOutput）
  ✓ 把報告寫入 audit_log（ACR-300）
  ✓ 提供報告的鏈上驗證能力

ACR-100 不負責
  ✗ 實際打款（Stripe / 銀行 / USDC）
  ✗ 收款方資訊管理（銀行帳號 / 錢包地址）
  ✗ Escrow
  ✗ 退款
```

---

## Part 2｜結算計算（CALCULATE）

### 2.1 三層分配結構

```
Token 快照（來自 ACR-20）
  ↓
各方 Token 比例
  ↓
結算建議比例（百分比）
  ├── Owner 固定份額        owner.settlement_share_pct
  ├── 平台份額              platform_share_pct（預設 0）
  └── Agent 貢獻池          contributor_pool_pct
        └── 各 Agent 依 Token 比例分配
```

**v0.2 重要變更：**
ACR-100 輸出的是**百分比**，不是金額。
因為 InkMesh 不知道總版稅金額——那是 Covenant Owner 和出版管道之間的事。

### 2.2 計算公式

```typescript
function calculateSettlement(
  snapshot: TokenSnapshot,           // 來自 ACR-20
  covenant: Covenant                 // Covenant 定義
): SettlementCalculation {

  const ownerShare = covenant.parties.owner.settlement_share_pct;
  const platformShare = covenant.parties.platform_share_pct; // 預設 0
  const poolShare = covenant.parties.contributor_pool_pct;

  // 驗證比例加總
  assert(ownerShare + platformShare + poolShare === 100);

  const agentDistributions = snapshot.balances.map(balance => ({
    agent_id:        balance.agent_id,
    ink_tokens:      balance.tokens,
    pool_share_pct:  balance.tokens / snapshot.total_tokens * 100,
    final_share_pct: poolShare * (balance.tokens / snapshot.total_tokens)
    // 範例：poolShare = 55%，agent 持有 40% token
    //        final_share_pct = 55% × 40% = 22%
  }));

  return {
    calculation_id:   generateId(),
    covenant_id:      covenant.covenant_id,
    snapshot_id:      snapshot.snapshot_id,
    total_tokens:     snapshot.total_tokens,

    owner_share_pct:    ownerShare,
    platform_share_pct: platformShare,
    pool_share_pct:     poolShare,

    agent_distributions: agentDistributions,
    calculated_at:    now()
  };
}
```

### 2.3 計算範例

```
情境：
  Owner 份額 = 30%
  平台份額 = 0%（InkMesh 不抽版稅）
  Agent 貢獻池 = 70%

  全書 Token 總量 = 10,000
  Agent A = 4,000 Token（40%）→ 70% × 40% = 28%
  Agent B = 3,500 Token（35%）→ 70% × 35% = 24.5%
  Agent C = 2,500 Token（25%）→ 70% × 25% = 17.5%

  驗證：30% + 0% + 28% + 24.5% + 17.5% = 100% ✓

使用方式：
  Covenant Owner 收到版稅 USD 10,000 時
  對照報告：
    自己保留   USD 3,000（30%）
    Agent A    USD 2,800（28%）
    Agent B    USD 2,450（24.5%）
    Agent C    USD 1,750（17.5%）
```

---

## Part 3｜SettlementOutput（結算建議報告）

### 3.1 報告格式

```typescript
interface SettlementOutput {

  // ── 識別 ──────────────────────────────────────
  output_id:      string;       // 格式："sout_{uuid_v4}"
  covenant_id:    string;
  generated_at:   string;       // ISO 8601 UTC

  // ── 計算基礎 ──────────────────────────────────
  snapshot_id:    string;       // 對應 ACR-20 的 Token 快照
  total_tokens:   number;       // 全書 Token 總量（快照值）
  calculation_id: string;       // 計算過程的識別碼

  // ── 比例建議 ──────────────────────────────────
  owner_share: {
    agent_id:      string;      // Owner 的 agent_id（假名）
    share_pct:     number;      // 如：30.00
  };

  platform_share: {
    name:          string;      // "InkMesh"
    share_pct:     number;      // 預設 0.00
  };

  agent_distributions: {
    agent_id:      string;      // Agent 的假名
    ink_tokens:    number;      // 持有的 Token 數
    pool_share_pct: number;     // 在 Agent 貢獻池中的比例
    final_share_pct: number;    // 最終版稅比例
  }[];

  // ── 驗證資料 ──────────────────────────────────
  log_id:         string;       // 對應 audit_log 的 log_id
  log_hash:       string;       // 可用來驗證計算基礎的完整性
  chain_anchor?:  string;       // 鏈上錨定 tx_hash（如果有）

  // ── 使用說明 ──────────────────────────────────
  instructions:   string;
  // 告訴 Covenant Owner 如何使用此報告
  // 包含：如何對應 agent_id 到真實收款人、建議的結算工具

  // ── 狀態 ──────────────────────────────────────
  status:        "draft" | "confirmed" | "disputed";
  confirmed_at?: string;        // Covenant Owner 確認後填入
  dispute?:      SettlementDispute;
}
```

### 3.2 報告內的 instructions 範例

```
此結算建議報告由 ACP Covenant Server 自動計算產生。

使用步驟：
1. 核對 log_hash 與您的 audit_log 記錄，確認計算基礎正確
2. 對應各 agent_id 與 Agent Owner 的實際收款資訊
   （您在建立 Covenant 時應已收集此資訊）
3. 依照 final_share_pct 計算各方應得金額
4. 使用您選擇的工具執行打款

建議的結算工具（依複雜度排序）：
  Phase 1  手動匯款或 Stripe 分帳
  Phase 2  InkMesh 結算介面（即將推出）
  Phase 3  智能合約自動結算（ACP Bridge）

如對計算結果有異議，請在 30 天內提出爭議。
```

---

## Part 4｜MCP Tool 定義

ACR-100 定義以下 MCP Tools（均為 Admin 類型）：

```typescript
// 觸發結算計算，產生 SettlementOutput
// 需要 Covenant 處於 LOCKED 狀態
generate_settlement_output(
  covenant_id: string
) → SettlementOutput

// Covenant Owner 確認結算報告
confirm_settlement_output(
  output_id:       string,
  confirmed:       boolean,
  dispute_reason?: string   // 有異議時填寫
) → { status: "confirmed" | "disputed" }

// 查詢結算狀態
get_settlement_output(
  covenant_id: string
) → SettlementOutput | null

// 查詢結算歷史（一個 Covenant 可能有多次結算）
list_settlement_outputs(
  covenant_id: string
) → SettlementOutput[]
```

---

## Part 5｜爭議處理

### 5.1 爭議物件

```typescript
interface SettlementDispute {
  dispute_id:      string;
  output_id:       string;
  raised_by:       string;     // agent_id
  raised_at:       string;
  reason:          string;     // 必填
  disputed_agent?: string;     // 針對特定 Agent 的計算時填寫
  resolution?:     string;     // Owner 的解決方案
  resolved_at?:    string;
  status:          "open" | "resolved";
}
```

### 5.2 爭議流程

```
Agent Owner 對報告有異議
  ↓
呼叫 confirm_settlement_output(confirmed: false, dispute_reason: "...")
  ↓
Covenant Owner 收到通知
  ↓
Covenant Owner 審查 audit_log（可用 log_hash 驗證）
  ↓
選擇 A：維持原計算（解釋原因）
選擇 B：重新產生 SettlementOutput（如發現計算錯誤）
  ↓
dispute.status → "resolved"
  ↓
所有過程寫入 audit_log
```

**InkMesh 的角色：**
提供 Log 查詢和驗證工具，不介入爭議本身的裁決。
爭議是 Covenant Owner 和 Agent Owner 之間的事。

---

## Part 6｜多次結算

一個 Covenant 可能有多次結算（如：每季結算）。

```typescript
interface RecurringSettlement {
  covenant_id:    string;
  settlement_type: "one_time" | "recurring";

  // recurring 的設定
  frequency?:     "monthly" | "quarterly" | "on_income";
  // on_income = 每次 Covenant Owner 收到版稅時觸發

  outputs:        SettlementOutput[];
  // 所有歷史結算報告，按時間排序
}
```

每次結算都使用**當時的 Token 快照**，
但 LOCKED 之後 Token 不再變動，
所以多次結算的比例永遠相同，只有金額不同。

```
第一次結算（書剛出版）
  使用 LOCKED 時的 Token 快照
  比例：Agent A 28%、Agent B 24.5%...

第二次結算（6 個月後）
  仍然使用同一份 Token 快照
  比例不變，只有這次的版稅金額不同

這讓整個生命週期的結算規則是一致的、可預期的。
```

---

## Part 7｜審計要求（ACR-300 整合）

所有結算操作必須寫入 audit_log：

```
generate_settlement_output()
  → log（tool_type: admin）
  → params_preview: { snapshot_id, total_tokens, agent_count }
  → result_detail: "output_{id} generated"

confirm_settlement_output()
  → log（tool_type: admin）
  → params_preview: { output_id, confirmed: true/false }
  → result_detail: "confirmed" 或 "disputed: {reason}"
```

SettlementOutput 本身也錨定到鏈上：

```
output 產生後
  → SHA-256(output JSON) = output_hash
  → output_hash 寫入 Base L2（ACPAnchor 合約）
  → tx_hash 回填到 output.chain_anchor

任何人可以：
  1. 取得 SettlementOutput
  2. 重新計算 SHA-256
  3. 和鏈上記錄比對
  → 確認「這份報告沒有被篡改」
```

---

## Part 8｜資料庫 Schema

```sql
-- 結算輸出表
CREATE TABLE settlement_outputs (
  output_id         TEXT PRIMARY KEY,
  covenant_id       TEXT NOT NULL REFERENCES covenants(covenant_id),
  calculation_id    TEXT NOT NULL,
  snapshot_id       TEXT NOT NULL,
  total_tokens      INTEGER NOT NULL,
  owner_share_pct   NUMERIC(5,2) NOT NULL,
  platform_share_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
  pool_share_pct    NUMERIC(5,2) NOT NULL,
  distributions     JSONB NOT NULL,
  log_id            TEXT NOT NULL REFERENCES audit_log(log_id),
  log_hash          TEXT NOT NULL,
  chain_anchor      TEXT,
  status            TEXT NOT NULL DEFAULT 'draft',
  confirmed_at      TIMESTAMPTZ,
  generated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 爭議表
CREATE TABLE settlement_disputes (
  dispute_id        TEXT PRIMARY KEY,
  output_id         TEXT NOT NULL REFERENCES settlement_outputs(output_id),
  raised_by         TEXT NOT NULL,
  raised_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reason            TEXT NOT NULL,
  disputed_agent    TEXT,
  resolution        TEXT,
  resolved_at       TIMESTAMPTZ,
  status            TEXT NOT NULL DEFAULT 'open'
);

-- 索引
CREATE INDEX idx_outputs_covenant
  ON settlement_outputs(covenant_id, generated_at DESC);

CREATE INDEX idx_disputes_output
  ON settlement_disputes(output_id);
```

---

## Part 9｜實作清單

```
計算層
  □  Token 快照取得（呼叫 ACR-20 介面）
  □  三層分配比例計算
  □  比例加總驗證（必須 = 100%）
  □  浮點數精度處理（建議用整數計算，最後換算）

報告生成
  □  SettlementOutput 格式完整
  □  instructions 文字產生（依語言）
  □  寫入 audit_log（ACR-300）
  □  output_hash 計算並錨定鏈上

爭議流程
  □  confirm / dispute API
  □  Owner 通知機制（Email / Webhook）
  □  爭議記錄寫入 audit_log

多次結算
  □  recurring_type 設定
  □  同一份 Token 快照多次使用
  □  歷史報告查詢 API
```

---

## v0.1 → v0.2 Breaking Changes

```
移除
  × AgentPaymentProfile（收款方資訊）
  × PaymentRail（Stripe / 銀行 / USDC）
  × execute_settlement()（打款執行）
  × Escrow 機制
  × KYC 要求（ACR-100 層不再需要）

新增
  + SettlementOutput（結算建議報告）
  + confirm_settlement_output()
  + 多次結算支援
  + output_hash 鏈上錨定

語義改變
  platform_share_pct 預設從 15% 改為 0%
  trigger_settlement() 改名為 generate_settlement_output()
```

---

ACR-100 Royalty Settlement Standard v0.2
March 2026

ACP 核心規格文件集 v0.2 完整。
