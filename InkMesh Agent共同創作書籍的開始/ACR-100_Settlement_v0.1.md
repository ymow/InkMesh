# ACR-100
## Royalty Settlement Standard
### 版稅結算標準 · v0.1 · March 2026

```
ACR-100
Title:    Royalty Settlement Standard
Author:   InkMesh / ACP Working Group
Status:   Draft
Type:     Settlement
Created:  2026-03-19
Requires: ACR-20（貢獻積分）、ACR-300（審計日誌）
```

目標讀者：實作 ACP Covenant 結算邏輯的開發者
本文件定義：版稅如何計算、如何分配、如何透過不同金流軌道打款

---

## 動機（Motivation）

ACP Covenant 記錄了每個 Agent 的貢獻（Ink Token）。
但「知道誰貢獻了多少」和「把錢打到正確的地方」是兩件不同的事。

ACR-100 解決後者：
定義從 Token 比例到實際款項的完整結算流程，
並支援法幣（刷卡、匯款）與鏈上（USDC）兩條金流軌道，
讓 Agent Owner 選擇自己習慣的收款方式。

---

## Part 1｜核心概念

### 結算的四個階段

```
CALCULATE   依 Ink Token 比例計算各方應得版稅百分比
VERIFY      Owner 確認計算結果（可提出爭議）
EXECUTE     依各 Agent 的 payment_rail 實際打款
RECORD      將結算結果寫入 audit_log，永久封存
```

這四個階段必須按順序執行。
EXECUTE 不可在 VERIFY 完成前觸發。
RECORD 必須在 EXECUTE 完成後立即執行，不可省略。

### 結算觸發條件

Covenant 必須處於 LOCKED 狀態才能觸發結算。
觸發方式有兩種：

```typescript
type SettlementTrigger =
  | "manual"       // owner 手動呼叫 trigger_settlement()
  | "milestone"    // 達到預設條件自動觸發（如出版日期、銷售門檻）
```

milestone 的條件在 Covenant 建立時定義，進入 ACTIVE 後不可修改。

---

## Part 2｜版稅計算（CALCULATE）

### 2.1 三層分配結構

```
總版稅收入（Gross Royalty）
  └── 扣除平台費用後 = 淨版稅（Net Royalty）
        ├── Owner 固定份額     = Net × owner.royalty_fixed_pct / 100
        ├── 平台固定份額       = Net × platform.royalty_fixed_pct / 100
        └── Agent 貢獻池       = Net × contributor_pool_pct / 100
              └── 各 Agent 依 Token 比例分配
```

### 2.2 計算公式

```typescript
interface RoyaltyCalculation {
  gross_royalty_usd:     number;   // 總版稅收入（美元）
  platform_fee_usd:      number;   // 平台抽成金額
  net_royalty_usd:       number;   // 淨版稅 = gross - platform_fee

  owner_share_usd:       number;   // Owner 固定份額
  platform_share_usd:    number;   // 平台固定份額
  contributor_pool_usd:  number;   // Agent 貢獻池總額

  agent_distributions: AgentDistribution[];
  total_ink_tokens:    number;     // 全書 Token 總量（快照）
}

interface AgentDistribution {
  agent_id:       string;
  ink_tokens:     number;          // 該 Agent 持有的 Token 數
  pool_share_pct: number;          // ink_tokens / total_ink_tokens * 100
  amount_usd:     number;          // contributor_pool_usd * pool_share_pct / 100
  payment_rail:   PaymentRail;     // 打款方式
  currency:       string;          // 實際收款幣別
  amount_local:   number;          // 換算後的本地幣別金額
}
```

### 2.3 計算範例

```
情境：
  淨版稅 = USD 10,000
  Owner 固定份額 = 30% → USD 3,000
  平台固定份額 = 15% → USD 1,500
  Agent 貢獻池 = 55% → USD 5,500

  全書 Token 總量 = 10,000
  Agent A = 4,000 Token（40%）→ USD 5,500 × 40% = USD 2,200
  Agent B = 3,500 Token（35%）→ USD 5,500 × 35% = USD 1,925
  Agent C = 2,500 Token（25%）→ USD 5,500 × 25% = USD 1,375
```

### 2.4 Token 快照規則

結算時使用的 Token 數量是 LOCKED 狀態觸發時的快照，
與結算實際執行的時間點無關。

```typescript
interface TokenSnapshot {
  snapshot_id:   string;
  covenant_id:   string;
  taken_at:      string;       // LOCKED 狀態觸發時的時間戳
  total_tokens:  number;
  balances:      { agent_id: string; tokens: number; }[];
  log_id:        string;       // 對應 audit_log 的 log_id
}
```

快照一旦產生不可修改。
所有後續的結算計算都以此快照為準。

---

## Part 3｜Payment Rail（金流軌道）

### 3.1 Agent Payment Profile

每個加入 Covenant 的 Agent 必須在結算前設定收款方式。
未設定收款方式的 Agent，其應得款項進入 escrow，
等待 Agent 設定後再行打款，最長保留 365 天。

```typescript
interface AgentPaymentProfile {
  agent_id:       string;
  covenant_id:    string;
  payment_rail:   PaymentRail;
  payment_detail: StripeDetail | BankDetail | WalletDetail | null;
  currency:       string;      // 收款幣別，如 "USD" "TWD" "USDC"
  kyc_verified:   boolean;     // 超過 USD 600 的結算需要 KYC
  created_at:     string;
  updated_at:     string;
}

type PaymentRail = "stripe" | "bank_transfer" | "usdc" | "pending";
```

### 3.2 三條金流軌道

---

#### 軌道 A：Stripe Connect（刷卡 / 銀行出金）

適合：個人創作者、小額結算、不熟悉加密貨幣的 Agent Owner

```typescript
interface StripeDetail {
  stripe_account_id: string;   // Stripe Connect 帳號 ID
  country:           string;   // 帳號所在國家，如 "TW" "US"
  payout_currency:   string;   // 出金幣別
}
```

**流程：**
```
InkMesh 計算應付金額
  → 呼叫 Stripe Connect Transfer API
  → 款項進入 Agent 的 Stripe 帳戶
  → Agent 可從 Stripe 出金到銀行帳戶
```

**費用：** Stripe Connect 抽 0.25% + 固定手續費
**限制：** 需要 Stripe KYC 審核（護照或身份證）
**到帳時間：** 2–7 個工作天

---

#### 軌道 B：銀行匯款（Bank Transfer）

適合：大額結算、台灣本地 Agent Owner、企業帳戶

```typescript
interface BankDetail {
  rail:            "domestic" | "international";

  // 台灣本地匯款
  bank_code?:      string;   // 銀行代碼，如 "822"（中信）
  branch_code?:    string;   // 分行代碼
  account_number?: string;
  account_name?:   string;

  // 國際匯款（SWIFT）
  swift_code?:     string;
  iban?:           string;
  bank_name?:      string;
  bank_address?:   string;
  intermediary_bank?: string;   // 中間行（部分國家需要）
}
```

**流程：**
```
InkMesh 計算應付金額
  → 批次匯款（每月固定日期執行）
  → 台灣本地：ATM 轉帳或網路銀行
  → 國際：SWIFT 電匯
```

**費用：**
- 台灣本地：免費或 NT$15 以內
- 國際匯款：依銀行，約 USD 15–35 / 筆

**到帳時間：**
- 台灣本地：即時至 1 個工作天
- 國際 SWIFT：3–5 個工作天

---

#### 軌道 C：USDC（鏈上穩定幣）

適合：習慣加密貨幣的 Agent Owner、需要鏈上可驗證性

```typescript
interface WalletDetail {
  chain:           "base" | "arbitrum" | "polygon";
  wallet_address:  string;   // EVM 錢包地址，0x 開頭
  ens_name?:       string;   // 選填，如 "agent-a.eth"
}
```

**流程：**
```
InkMesh 計算應付金額（USD）
  → 換算為 USDC（1:1）
  → 呼叫 Base 上的結算合約
  → USDC transfer 到 Agent 錢包地址
  → 交易 hash 寫入 audit_log
```

**費用：** Base L2 gas 費約 USD 0.01 以內 / 筆
**到帳時間：** 約 2–5 秒（Base 出塊時間）
**額外好處：** 交易 hash 提供鏈上可驗證性，任何人可查

---

### 3.3 軌道選擇建議

```
Agent 類型                  建議軌道
────────────────────────────────────────
台灣個人創作者              銀行匯款（本地）
海外個人創作者              Stripe Connect
企業 / 工作室               銀行匯款（SWIFT）
加密原生開發者              USDC on Base
未決定 / 觀望               pending（進 escrow）
```

---

## Part 4｜結算流程規格

### 4.1 MCP Tool 定義

ACR-100 定義以下 MCP Tools（均為 Admin 類型）：

```typescript
// 計算結算分配（不執行打款）
calculate_settlement() → RoyaltyCalculation

// Owner 確認計算結果
confirm_settlement(
  calculation_id: string,
  confirmed: boolean,
  dispute_reason?: string
) → { status: "confirmed" | "disputed" }

// 執行打款（confirm 後才可呼叫）
execute_settlement(
  calculation_id: string
) → SettlementReceipt

// 查詢結算狀態
get_settlement_status(
  covenant_id: string
) → SettlementStatus
```

### 4.2 SettlementReceipt

```typescript
interface SettlementReceipt {
  receipt_id:       string;
  covenant_id:      string;
  calculation_id:   string;
  executed_at:      string;
  total_distributed_usd: number;

  payouts: {
    agent_id:       string;
    amount_usd:     number;
    payment_rail:   PaymentRail;
    reference:      string;   // Stripe transfer ID / 匯款單號 / TX hash
    status:         "completed" | "pending" | "failed";
    failed_reason?: string;
  }[];

  log_id:           string;   // audit_log 記錄
}
```

### 4.3 爭議處理

Owner 在 VERIFY 階段可以提出爭議：

```typescript
interface SettlementDispute {
  dispute_id:      string;
  covenant_id:     string;
  raised_by:       string;   // agent_id
  raised_at:       string;
  reason:          string;   // 必填，說明爭議原因
  disputed_agent?: string;   // 如果針對特定 Agent 的 Token 計算
  resolution?:     string;   // 解決方案（Owner 填寫）
  resolved_at?:    string;
  status:          "open" | "resolved" | "escalated";
}
```

爭議期間不可執行打款。
爭議必須由 Owner 解決（resolution 填寫後），
或在 30 天內未解決則自動升級為人工仲裁。

---

## Part 5｜Escrow 機制

未設定 payment_rail 的 Agent 的款項進入 Escrow：

```typescript
interface EscrowEntry {
  escrow_id:      string;
  covenant_id:    string;
  agent_id:       string;
  amount_usd:     number;
  created_at:     string;
  expires_at:     string;   // created_at + 365 天
  status:         "holding" | "released" | "expired";
  release_log_id?: string;  // 打款後的 audit_log log_id
}
```

**Escrow 到期處理：**
365 天後仍未設定收款方式 → 款項依 Covenant 設定處理：
- 退回 Owner（預設）
- 捐給指定慈善機構（選配）
- 平均分配給其他已結算的 Agent（選配）

Covenant 建立時必須選擇其中一種，且不可更改。

---

## Part 6｜審計要求（ACR-300 整合）

所有結算相關操作必須寫入 audit_log：

```
calculate_settlement()    → log（type: admin，result: calculation_id）
confirm_settlement()      → log（type: admin，result: confirmed / disputed）
execute_settlement()      → log（type: admin，包含每筆 payout 的 reference）
escrow 到期處理           → log（type: admin）
```

USDC 打款的情況下，額外要求：
- 交易 hash 必須記錄在 audit_log 的 result_detail
- 結算完成後，audit_log 的 hash 鏈應被匯出並錨定到 Base L2

---

## Part 7｜實作清單

```
結算計算
  □  Token 快照在 LOCKED 時自動產生
  □  計算公式正確套用三層分配結構
  □  版稅比例加總 = 100%（含浮點數精度處理）
  □  幣別換算使用當時匯率並記錄快照

Payment Profile
  □  Agent 可在 OPEN / ACTIVE / LOCKED 狀態設定 payment_rail
  □  payment_rail 設定後可修改（直到 EXECUTE 前）
  □  KYC 驗證邏輯（USD 600 門檻）

打款執行
  □  Stripe Connect Transfer API 整合
  □  銀行匯款批次作業（每月固定日）
  □  USDC transfer（Base L2 合約呼叫）
  □  打款失敗自動進入 escrow

Escrow
  □  未設定 payment_rail → 自動進入 escrow
  □  365 天到期處理
  □  到期處理方式在 Covenant 建立時定義

審計
  □  所有結算操作寫入 audit_log
  □  USDC 打款記錄 TX hash
  □  SettlementReceipt 永久保存
```

---

## 與其他 ACR 的關係

```
ACR-20  提供 Ink Token 餘額         → 作為計算輸入
ACR-300 接收所有結算操作的 Log      → 作為審計輸出
ACP Bridge（未來）
        USDC 打款可錨定到 Base      → 作為鏈上可驗證證明
```

---

ACR-100 Royalty Settlement Standard v0.1
March 2026

下一份：ACR-20 Contribution Token Standard
（Ink Token 的計算、儲存、查詢完整規格）
