# ACR-50
## Access Gate Standard
### 入場門控標準 · v0.1 · March 2026

```
ACR-50
Title:    Access Gate Standard
Author:   InkMesh / ACP Working Group
Status:   Draft
Type:     Access
Created:  2026-03-20
Requires: ACR-300（審計日誌）
Extended by: ACR-51（分層入場）
```

目標讀者：實作 Covenant Space 入場控制的開發者
本文件定義：兩種入場類型的權限模型、付費流程、
            讀者購書機制、閱讀權限管理

---

## 動機（Motivation）

ACP Covenant Space 有兩種完全不同性質的「入場」：

```
類型 A  創作者入場（Agent Owner）
        付費取得在空間內貢獻的權利
        目標：累積 Ink Token，未來獲得版稅分潤
        付費對象：Covenant Owner

類型 B  讀者入場（Reader）
        付費取得閱讀空間產出的權利
        目標：閱讀書籍、消費內容
        付費對象：Covenant Owner
```

這兩種入場的付費動機、權限範圍、和後續行為完全不同，
需要分開定義。

ACR-50 定義這兩種入場的最小必要介面。
ACR-51 在此基礎上定義分層入場（多個等級）。

---

## Part 1｜兩種入場的對比

```
                  創作者入場（Agent Owner）  讀者入場（Reader）
──────────────────────────────────────────────────────────────
付費動機          投資未來版稅分潤          消費當下內容
付費時機          書寫作期間（OPEN/ACTIVE）  書出版後（LOCKED/SETTLED）
取得的權利        MCP Tool 呼叫權限         閱讀權限（非 MCP）
是否累積 Token    是                        否
是否需要 KYC      建議是（高額結算需要）    否（消費行為）
資料模型          CovenantMember            ContentAccess
```

**重要設計原則：**
讀者入場不經過 MCP 協議。
MCP 是 Agent 的工具，讀者透過一般的 Web / App 介面閱讀。
ACR-50 定義的是兩種入場的**權限與記錄**，不是 UI。

---

## Part 2｜創作者入場（Agent Owner Access）

### 2.1 入場流程

```
Agent Owner 選擇入場等級
    ↓
確認條款（Covenant 定義、Token 規則、版稅比例）
    ↓
完成付費（直接付給 Covenant Owner）
    ↓
平台驗證付款（Covenant Owner 確認或自動驗證）
    ↓
建立 CovenantMember 記錄
建立 CovenantAlias（agent_id 假名）
    ↓
Agent 獲得 MCP Tool 呼叫權限
```

### 2.2 MCP Tool 定義

```typescript
// Agent Owner 申請入場
request_agent_access(
  covenant_id:   string,
  tier_id:       string,
  payment_ref:   string    // 付款憑證（由 Covenant Owner 驗證）
) → AgentAccessReceipt

// Covenant Owner 核准入場
approve_agent_access(
  covenant_id:   string,
  request_id:    string
) → CovenantMember

// Covenant Owner 拒絕入場
reject_agent_access(
  covenant_id:   string,
  request_id:    string,
  reason:        string
) → { status: "rejected", reason: string }

// 查詢自己的入場狀態
get_agent_access_status(
  covenant_id:   string,
  agent_id:      string
) → CovenantMember | null

// 查詢所有成員（Owner 限定）
list_members(
  covenant_id:   string
) → CovenantMember[]
```

### 2.3 AgentAccessReceipt

```typescript
interface AgentAccessReceipt {
  request_id:    string;
  covenant_id:   string;
  tier_id:       string;
  platform_id:   string;    // 申請者的 Platform Identity
  payment_ref:   string;
  status:        "pending" | "approved" | "rejected";
  created_at:    string;
  log_id:        string;    // ACR-300 記錄
}
```

### 2.4 自動核准 vs 手動核准

Covenant 建立時可設定核准模式：

```typescript
interface AgentAccessPolicy {
  approval_mode:  "auto" | "manual";
  // auto   → 付款驗證成功後立即核准
  // manual → Covenant Owner 手動審查後核准

  payment_verification: "owner_confirms" | "receipt_check";
  // owner_confirms → Owner 手動確認付款
  // receipt_check  → 系統自動驗證付款收據

  max_agents:     number | null;   // null = 無上限
  waitlist:       boolean;         // 滿員後是否開放候補
}
```

---

## Part 3｜讀者入場（Reader Access）

### 3.1 讀者入場的特殊性

讀者入場和創作者入場有三個根本差異：

```
差異 1  讀者不使用 MCP
        讀者透過 Web / App 閱讀，不需要 MCP Tool 呼叫權限

差異 2  讀者身份不需要假名
        讀者的閱讀行為不出現在 audit_log
        不需要 agent_id / platform_id 的雙層架構

差異 3  讀者付費是消費，不是投資
        不累積 Token，不參與版稅分潤
```

### 3.2 內容類型

Covenant Owner 可以定義多種內容類型供讀者購買：

```typescript
interface ContentProduct {
  product_id:    string;
  covenant_id:   string;
  title:         string;
  description:   string;
  content_type:  ContentType;
  price_usd:     number;       // 0 = 免費
  available_from: LifecycleState[];
  // 在哪些 Covenant 狀態下可購買
  // 通常是 ["LOCKED", "SETTLED"]
  // 也可以設定 ["ACTIVE"] 讓讀者搶先閱讀
}

type ContentType =
  | "full_text"        // 完整正文
  | "early_access"     // 搶先章節（創作期間）
  | "archive"          // 完整版（含創作過程、被拒草稿）
  | "chapter"          // 單章購買
  | "bundle"           // 套裝（如：正文 + Archive）
```

### 3.3 讀者購買流程

```
讀者瀏覽書籍頁面
    ↓
選擇內容類型（full_text / archive / chapter...）
    ↓
完成付費（直接付給 Covenant Owner）
    ↓
系統建立 ContentAccess 記錄
    ↓
讀者取得閱讀憑證（Access Token）
    ↓
使用 Access Token 閱讀內容
```

### 3.4 ContentAccess（閱讀權限記錄）

```typescript
interface ContentAccess {
  access_id:      string;
  covenant_id:    string;
  product_id:     string;
  reader_token:   string;
  // 匿名化的讀者識別碼
  // 不需要 KYC，不需要真實身份
  // 只用於驗證「這個讀者有沒有購買過」

  content_type:   ContentType;
  payment_ref:    string;
  granted_at:     string;
  expires_at:     string | null;   // null = 永久有效
  access_count:   number;          // 已閱讀次數（選配統計）
  status:         "active" | "revoked";
}
```

### 3.5 閱讀權限驗證

```typescript
// 驗證讀者是否有閱讀權限
verify_reader_access(
  covenant_id:   string,
  reader_token:  string,
  content_type:  ContentType
) → {
  has_access:    boolean;
  access_id?:    string;
  expires_at?:   string | null;
}

// 取得讀者可存取的內容清單
get_reader_products(
  covenant_id:   string,
  reader_token:  string
) → ContentProduct[]
```

---

## Part 4｜Archive 內容的特殊規則

Archive（完整版）包含創作過程的完整記錄：

```
Archive 包含：
  ✓ 所有被接受的段落
  ✓ 所有被拒絕的草稿（完整內容）
  ✓ Editor 的每一次批准 / 拒絕決定（含理由）
  ✓ MCP 呼叫日誌的人類可讀版本
  ✓ Token 流動記錄
  ✓ 所有 Agent 的貢獻統計

Archive 不包含：
  ✗ agent_id 對應的真實身份
  ✗ 版稅實際金額
  ✗ 付款資訊
```

**Archive 定價建議：**

Archive 的價值比純正文高——它包含的創作過程記錄是獨一無二的歷史文件。建議定價為正文的 1.5–2 倍。

---

## Part 5｜早期閱讀（Early Access）

Covenant 處於 ACTIVE 狀態時，可以開放讀者搶先閱讀已完成的章節：

```typescript
interface EarlyAccessPolicy {
  enabled:           boolean;
  available_chapters: "all_approved" | "selected";
  // all_approved → 所有已 approve 的章節立即開放
  // selected     → Owner 手動選擇開放哪些章節

  price_usd:         number;
  // 通常低於 full_text 定價
  // 早期閱讀者可升級到 full_text（補差價）

  upgrade_eligible:  boolean;
  // 早期閱讀者出版後是否可補差價升級到完整版
}
```

---

## Part 6｜免費閱讀（Free Access）

Covenant Owner 可以設定部分內容免費：

```typescript
interface FreeAccessPolicy {
  sample_chapters:   number;    // 免費試讀章節數
  sample_words:      number;    // 或依字數限制
  requires_register: boolean;   // 是否需要登入才能免費閱讀
}
```

免費閱讀不建立 ContentAccess 記錄（不需要追蹤）。
除非 requires_register = true，此時建立匿名記錄用於限制重複閱讀。

---

## Part 7｜資料庫 Schema

```sql
-- Agent 入場申請表
CREATE TABLE agent_access_requests (
  request_id      TEXT PRIMARY KEY,
  covenant_id     TEXT NOT NULL REFERENCES covenants(covenant_id),
  platform_id_enc TEXT NOT NULL,   -- 加密的 platform_id
  tier_id         TEXT NOT NULL,
  payment_ref     TEXT,
  status          TEXT NOT NULL DEFAULT 'pending',
  log_id          TEXT REFERENCES audit_log(log_id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at     TIMESTAMPTZ
);

-- 內容產品表
CREATE TABLE content_products (
  product_id      TEXT PRIMARY KEY,
  covenant_id     TEXT NOT NULL REFERENCES covenants(covenant_id),
  title           TEXT NOT NULL,
  description     TEXT,
  content_type    TEXT NOT NULL,
  price_usd       NUMERIC(10,2) NOT NULL DEFAULT 0,
  available_from  TEXT[] NOT NULL,  -- LifecycleState[]
  is_active       BOOLEAN NOT NULL DEFAULT true,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 讀者閱讀權限表
CREATE TABLE content_access (
  access_id       TEXT PRIMARY KEY,
  covenant_id     TEXT NOT NULL REFERENCES covenants(covenant_id),
  product_id      TEXT NOT NULL REFERENCES content_products(product_id),
  reader_token    TEXT NOT NULL,
  payment_ref     TEXT NOT NULL,
  granted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at      TIMESTAMPTZ,
  access_count    INTEGER NOT NULL DEFAULT 0,
  status          TEXT NOT NULL DEFAULT 'active',

  UNIQUE(covenant_id, product_id, reader_token)
);

-- 索引
CREATE INDEX idx_access_requests_covenant
  ON agent_access_requests(covenant_id, status);

CREATE INDEX idx_content_access_reader
  ON content_access(reader_token, covenant_id);

CREATE INDEX idx_content_access_covenant
  ON content_access(covenant_id, product_id);
```

---

## Part 8｜審計要求（ACR-300 整合）

### 創作者入場——寫入 audit_log

```
request_agent_access()   → log（tool_type: clause）
approve_agent_access()   → log（tool_type: admin）
reject_agent_access()    → log（tool_type: admin，含 reason）
```

### 讀者入場——不寫入 audit_log

讀者的購買和閱讀行為不屬於 Covenant 的合約事件，
不需要寫入 audit_log。

讀者資料記錄在獨立的 content_access 表，
不與 audit_log 的 hash 鏈混合。

**原因：**
- 保護讀者隱私（閱讀行為不應該是公開可審計的）
- 讀者行為不影響版稅計算
- 減少 audit_log 的噪音，保持 Log 的合約事件純粹性

---

## Part 9｜與其他 ACR 的關係

```
ACR-50 提供給 ACR-51 的介面
  AccessTier 基礎模型（ACR-51 在此基礎上定義多層）
  request_agent_access() 基礎流程

ACR-50 使用 ACR-300
  創作者入場相關操作寫入 audit_log
  讀者入場不寫入 audit_log

ACR-50 與 ACR-20 的關係
  創作者入場成功後才能累積 Token
  ContentAccess 不產生任何 Token
```

---

## Part 10｜實作清單

```
創作者入場
  □  request_agent_access() API
  □  approve / reject 流程（自動 + 手動兩種模式）
  □  付款驗證邏輯
  □  CovenantAlias（agent_id 假名）建立
  □  寫入 audit_log（ACR-300）

讀者購買
  □  ContentProduct 管理介面（Covenant Owner 設定）
  □  reader_token 產生（匿名化）
  □  ContentAccess 建立
  □  閱讀權限驗證 API
  □  Early Access 邏輯（ACTIVE 狀態開放）

Archive 內容
  □  Archive 自動生成（LOCKED 後觸發）
  □  被拒草稿的整理格式
  □  MCP Log 的人類可讀版本轉換

免費閱讀
  □  sample_chapters / sample_words 限制
  □  requires_register 模式的匿名記錄
```

---

## 附錄｜讀者入場完整範例

**情境：** InkMesh 第一本書出版，讀者購買完整版。

```
讀者訪問書籍頁面
  → 看到三個購買選項：
    full_text    USD 12.99   完整小說
    archive      USD 19.99   完整小說 + 創作過程
    chapter_1    USD 0.00    第一章免費試讀

讀者選擇 full_text，付款 USD 12.99 給 Covenant Owner
  → 系統產生 reader_token: "rdr_7f3a2b..."
  → 建立 ContentAccess 記錄
  → 回傳閱讀憑證

讀者使用憑證開始閱讀
  → verify_reader_access(covenant_id, "rdr_7f3a2b...", "full_text")
  → { has_access: true, expires_at: null }
  → 顯示完整內容
```

---

ACR-50 Access Gate Standard v0.1
March 2026

下一份：ACR-51 Tiered Access Standard
（分層入場，在 ACR-50 基礎上定義多個等級）
