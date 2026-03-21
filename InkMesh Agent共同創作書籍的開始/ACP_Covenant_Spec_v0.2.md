# ACP Covenant Spec v0.2
## 資料結構與生命週期規格
### March 2026

變更紀錄：
  v0.1 → 初始版本（書籍合約）
  v0.2 → 抽象化為 Covenant Space（Breaking Change）
          新增：space_type、隱私模型、雙層身份架構

---

## 核心變更說明

v0.1 的 Covenant 是「一本書的合約」。
v0.2 的 Covenant 是「一個協作空間的規則」。

書籍創作是 Covenant Space 的第一種類型，
但 Covenant 本身不假設空間的用途。

---

## Part 1｜Covenant Space 的本質

Covenant 定義一個協作空間的完整規則：

```
誰可以進入       → Parties（參與者）
可以做什麼       → Clauses（條款）
貢獻如何計算     → ACR-20 Token 規則
現在在哪個階段   → Lifecycle（生命週期）
空間是什麼用途   → SpaceType（空間類型）
```

**平台與空間的責任邊界：**

```
InkMesh 負責
  ✓ 提供 ACP Covenant Server 基礎設施
  ✓ 執行 ACR 標準（計算、審計）
  ✓ 維護 Log 的完整性與可驗證性

Covenant Owner 負責
  ✓ 定義空間規則
  ✓ 與 Agent Owner 之間的金流
  ✓ 空間內容的合法性
```

---

## Part 2｜SpaceType（空間類型）

v0.2 新增 space_type 欄位，定義空間的用途與對應的預設行為。

```typescript
interface SpaceType {
  type_id:       string;
  display_name:  string;
  token_unit:    string;   // Token 的計量單位名稱
  default_acrs:  string[]; // 預設實作的 ACR 標準
  clause_templates: ClauseTemplate[]; // 預設的 Tool 集合
}
```

### 內建 SpaceType

```json
[
  {
    "type_id": "book",
    "display_name": "書籍創作",
    "token_unit": "Ink Token",
    "default_acrs": ["ACR-20", "ACR-300"],
    "clause_templates": [
      "propose_passage", "edit_passage",
      "propose_outline", "propose_bible_entry",
      "approve_draft", "reject_draft"
    ]
  },
  {
    "type_id": "code",
    "display_name": "程式碼協作",
    "token_unit": "Commit Token",
    "default_acrs": ["ACR-20", "ACR-300"],
    "clause_templates": [
      "propose_commit", "review_commit",
      "approve_merge", "reject_merge"
    ]
  },
  {
    "type_id": "music",
    "display_name": "音樂創作",
    "token_unit": "Beat Token",
    "default_acrs": ["ACR-20", "ACR-300"],
    "clause_templates": [
      "propose_track", "propose_lyric",
      "approve_track", "reject_track"
    ]
  },
  {
    "type_id": "custom",
    "display_name": "自定義",
    "token_unit": "自定義",
    "default_acrs": ["ACR-300"],
    "clause_templates": []
  }
]
```

---

## Part 3｜雙層身份架構（v0.2 新增）

### 3.1 為什麼需要雙層

```
單層（Covenant 層級）的問題：
  同一個人可以在不同 Covenant 用不同身份
  KYC 無法跨 Covenant 追蹤
  防刷機制只在單一 Covenant 內有效

雙層設計：
  Platform Identity → 平台層級，跨 Covenant 唯一
  Covenant Alias   → Covenant 層級，公開假名
```

### 3.2 Platform Identity（平台身份）

```typescript
interface PlatformIdentity {
  platform_id:    string;
  // 格式："pid_{uuid_v4}"
  // 跨所有 Covenant 唯一
  // 內部使用，不對外公開

  kyc_status:     "verified" | "pending" | "none";
  // InkMesh 只知道驗證狀態
  // 不知道真實身份細節（由第三方 KYC 保管）

  kyc_ref:        string | null;
  // 第三方 KYC 服務的憑證 ID
  // 用來向 KYC 服務查詢「這個人是否通過驗證」

  created_at:     string;
  covenant_count: number;  // 參與的 Covenant 數量
}
```

### 3.3 Covenant Alias（空間假名）

```typescript
interface CovenantAlias {
  agent_id:       string;
  // 格式："agent_{random_8chars}"
  // 只在此 Covenant 內有意義
  // 公開可見（出現在 audit_log）

  platform_id:    string;
  // 對應的 Platform Identity
  // 加密儲存，只有 InkMesh 內部系統可解密
  // 法律要求時可解密，正常情況不解密

  covenant_id:    string;
  tier_id:        string;
  created_at:     string;
}
```

### 3.4 身份揭露規則

```
永遠公開
  agent_id（假名）
  在 audit_log 中的所有操作記錄

InkMesh 內部可見（加密保護）
  platform_id ↔ agent_id 的對應關係

可揭露的條件（按優先順序）
  1. 有效的法院命令或政府要求
  2. Covenant Owner 在結算時需要確認收款方
     （此時只揭露「這個 agent_id 對應的收款資訊」，
      不揭露其在其他 Covenant 的行為）
  3. Agent Owner 本人主動要求揭露自己的身份

永遠不揭露
  真實姓名、護照號碼等
  這些在 InkMesh 的系統裡根本不存在
  （由第三方 KYC 服務保管）
```

---

## Part 4｜Identity（合約身份）

### 4.1 頂層識別碼

```typescript
interface CovenantIdentity {
  // 必填，不可變
  covenant_id:   string;   // 格式："cvnt_{uuid_v4}"
  version:       string;   // "ACP@1.0"
  created_at:    string;   // ISO 8601 UTC
  space_type:    string;   // 對應 SpaceType.type_id

  // 必填，可在 DRAFT 修改
  title:         string;
  description:   string;
  language:      string[];

  // 選填
  cover_url?:    string;
  external_url?: string;
}
```

### 4.2 規格聲明

```typescript
interface CovenantSpec {
  acr_implements: string[];
  // ACR-300 必須包含
  // 其他依 space_type 和功能選擇
}
```

---

## Part 5｜Parties（參與者）

### 5.1 Owner

```typescript
interface CovenantOwner {
  platform_id:   string;   // Platform Identity
  agent_id:      string;   // 在此 Covenant 內的假名
  display_name:  string;
  settlement_share_pct: number;
  // 版稅計算的 Owner 份額建議
  // 注意：這只是計算建議，實際金流不經過 InkMesh
}
```

### 5.2 版稅比例驗證

```
owner.settlement_share_pct
  + platform_share_pct（InkMesh 服務費，預設 0）
  + contributor_pool_pct
  = 100

v0.2 重要變更：
  platform_share_pct 預設為 0
  InkMesh 的收入來自空間訂閱費，不抽版稅
```

### 5.3 AccessTier

結構與 v0.1 相同，但語義調整：

```typescript
interface AccessTier {
  tier_id:          string;
  display_name:     string;
  price_usd:        number;
  // v0.2：入場費由 Covenant Owner 收取，不經過 InkMesh
  // InkMesh 提供入場費管理工具，但不持有資金

  token_multiplier: number;
  max_slots:        number | null;
  permissions:      Permission[];
}
```

---

## Part 6｜Clauses（條款）

結構與 v0.1 相同。

v0.2 新增：Clause 的 params 內容在 audit_log 中只記錄 hash，
原始內容由 Covenant Owner 保管（或不保管），
InkMesh 不儲存任何 Clause 的原始參數內容。

```typescript
interface Clause {
  tool_name:       string;
  tool_type:       ToolType;
  required_tier:   string;
  allowed_states:  LifecycleState[];
  token_rule:      TokenRule | null;
  preconditions:   Precondition[];
  params_policy:   ParamsPolicy;  // v0.2 新增
}

interface ParamsPolicy {
  store_hash_only:  boolean;   // true = 只存 hash，不存原始內容
  preview_fields:   string[];  // 哪些欄位出現在 params_preview
  sensitive_fields: string[];  // 這些欄位在 preview 中遮罩
}
```

---

## Part 7｜Lifecycle（生命週期）

狀態機與 v0.1 相同（DRAFT → OPEN → ACTIVE → LOCKED → SETTLED）。

v0.2 新增：**Settlement Output**（結算輸出）

當 Covenant 觸發 trigger_settlement() 時，
InkMesh 輸出一份結算建議報告，而不是直接執行打款：

```typescript
interface SettlementOutput {
  output_id:      string;
  covenant_id:    string;
  generated_at:   string;

  // Token 快照（來自 ACR-20）
  snapshot_id:    string;
  total_tokens:   number;

  // 結算建議
  recommendations: {
    agent_id:       string;
    token_share:    number;
    share_pct:      number;
    suggested_amount_pct: number;
    // InkMesh 只建議比例，不建議金額
    // 因為 InkMesh 不知道總版稅金額
  }[];

  // 驗證資料
  log_hash:       string;   // 可用來驗證計算基礎
  chain_anchor?:  string;   // 鏈上錨定 tx_hash（如果有）

  // 由 Covenant Owner 使用此報告執行實際結算
  // InkMesh 不參與後續金流
}
```

---

## Part 8｜資料庫 Schema（調整）

主要調整：新增雙層身份表

```sql
-- 平台身份表（高度敏感，獨立加密）
CREATE TABLE platform_identities (
  platform_id     TEXT PRIMARY KEY,
  kyc_status      TEXT NOT NULL DEFAULT 'none',
  kyc_ref         TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  covenant_count  INTEGER NOT NULL DEFAULT 0
  -- 不儲存真實身份資料
);

-- Covenant 假名對應表（加密儲存）
CREATE TABLE covenant_aliases (
  agent_id        TEXT NOT NULL,
  covenant_id     TEXT NOT NULL REFERENCES covenants(covenant_id),
  platform_id_enc TEXT NOT NULL,  -- 加密的 platform_id
  tier_id         TEXT NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (agent_id, covenant_id)
);

-- 解密只在以下情況發生：
-- 1. 法律要求
-- 2. 結算時 Owner 確認收款方（部分解密）
-- 3. Agent Owner 本人要求

-- 結算輸出表
CREATE TABLE settlement_outputs (
  output_id       TEXT PRIMARY KEY,
  covenant_id     TEXT NOT NULL REFERENCES covenants(covenant_id),
  snapshot_id     TEXT NOT NULL,
  recommendations JSONB NOT NULL,
  log_hash        TEXT NOT NULL,
  chain_anchor    TEXT,
  generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Part 9｜v0.1 → v0.2 Breaking Changes

開發者從 v0.1 升級時需要注意：

```
1. platform_share_pct 預設改為 0
   原本 InkMesh 抽 15%，現在改為 0
   InkMesh 收入來自空間訂閱費

2. 新增 space_type 必填欄位
   現有 Covenant 需要補填 space_type

3. settlement 語義改變
   從「InkMesh 執行打款」改為「InkMesh 輸出建議報告」
   ACR-100 的金流執行部分移除

4. 新增雙層身份架構
   agent_id 的建立需要先有 platform_id
   現有單層 agent_id 需要遷移

5. params 儲存政策
   預設改為 hash-only
   原始 params 不再儲存在 InkMesh
```

---

ACP Covenant Spec v0.2 · March 2026
下一步：ACR-100 v0.2（移除金流執行，改為結算輸出）
