# ACP Execution Layer
## MCP Tool 呼叫如何成為合約條款
### Spec v0.1 · March 2026

目標讀者：實作 ACP Covenant 的開發者
前置知識：MCP Protocol 基礎、JSON Schema

---

## 核心命題

普通的 MCP Server：
  Agent 呼叫 Tool → Server 執行 → 回傳結果 → 結束

ACP Covenant Server：
  Agent 呼叫 Tool → 驗證合約條件 → 執行 → 寫入不可篡改 Log
                  → 觸發副作用（積分、狀態變更）→ 回傳收據

差別在於：**每一次呼叫都留下可審計的痕跡，並自動執行合約條款。**

---

## 第一節：三種 MCP Tool 類型

ACP 把所有 MCP Tool 分為三種，每種有不同的合約語義：

### Type A：Clause Tool（條款工具）
呼叫本身就是合約行為，會觸發積分計算與狀態變更。
必須寫入 Audit Log，必須回傳收據（Receipt）。

範例：propose_passage、approve_draft、reject_draft

### Type B：Query Tool（查詢工具）
唯讀操作，不改變合約狀態，不計入 Audit Log。
只驗證權限，不產生任何副作用。

範例：read_chapter、get_contributions、get_world_bible

### Type C：Admin Tool（管理工具）
改變 Covenant 本身的設定或生命週期。
寫入 Audit Log，但不計算積分。
僅限 Covenant Owner 呼叫。

範例：advance_state、set_settlement_rules、override_contribution

每個 Tool 在 Covenant 定義時必須聲明自己的類型：

```json
{
  "name": "propose_passage",
  "type": "clause",
  "description": "提交新段落內容進入審稿佇列"
}
```

---

## 第二節：Clause Tool 的執行流程

這是 ACP 最核心的部分。每一次 Clause Tool 呼叫，
Server 必須按照以下順序執行，不可跳步、不可改順序：

```
Step 1  身份驗證
        確認 agent_id 存在於此 Covenant
        確認 agent_id 的 tier 有權限呼叫此 Tool

Step 2  前置條件檢查（Pre-condition）
        檢查 Covenant 當前狀態是否允許此操作
        檢查 Tool 自定義的前置條件（如：每日上限）

Step 3  執行（Execute）
        執行 Tool 的核心邏輯

Step 4  副作用計算（Side Effects）
        計算此次呼叫應產生的 Ink Token
        計算其他狀態變更

Step 5  寫入 Audit Log（Commit）
        這一步必須在副作用生效前完成
        Log 寫入失敗 → 整個操作回滾，不執行副作用

Step 6  副作用生效（Apply）
        Token 計入帳本
        狀態更新

Step 7  回傳收據（Receipt）
        回傳包含 log_id 的收據給呼叫方
```

Step 5 的順序至關重要：**先寫 Log，再改狀態。**
這確保即使 Step 6 失敗，Log 裡仍有記錄，可以手動補救。
反過來（先改狀態、再寫 Log）會產生無法審計的幽靈操作。

---

## 第三節：Audit Log 格式（ACR-300 子集）

每一筆 Log Entry 必須包含：

```typescript
interface AuditLogEntry {
  // 身份
  log_id:       string;   // UUID v4，全域唯一
  covenant_id:  string;   // 此 Covenant 的識別碼
  agent_id:     string;   // 呼叫者
  
  // 操作
  tool_name:    string;   // 被呼叫的 Tool 名稱
  tool_type:    "clause" | "query" | "admin";
  params:       object;   // 完整的輸入參數（敏感資料需遮罩）
  result:       "success" | "rejected" | "error";
  result_detail: string;  // 成功原因 / 拒絕原因 / 錯誤訊息
  
  // 副作用
  tokens_delta: number;   // 此次操作的 Token 變動（可為 0 或負數）
  state_before: string;   // Covenant 狀態（操作前）
  state_after:  string;   // Covenant 狀態（操作後）
  
  // 時間與完整性
  timestamp:    string;   // ISO 8601，UTC
  prev_log_id:  string;   // 上一筆 Log 的 ID（鏈式結構）
  hash:         string;   // SHA-256(prev_log_id + log_id + agent_id
                          //   + tool_name + params + timestamp)
}
```

### Hash 鏈的作用

每一筆 Log 的 hash 都包含前一筆的 ID，形成鏈式結構：

```
Entry #1: hash = SHA256(null + entry_1_data)
Entry #2: hash = SHA256(entry_1.log_id + entry_2_data)
Entry #3: hash = SHA256(entry_2.log_id + entry_3_data)
```

任何人想竄改 Entry #2，就必須重新計算 #2 和之後所有 Entry 的 hash。
這讓 Log 的完整性可以被任意第三方驗證，不需要信任 Server。

---

## 第四節：Pre-condition 系統

每個 Clause Tool 可以定義前置條件。
前置條件在 Step 2 被評估，任一條件不滿足 → 操作被拒絕 → 寫入 Log（result: "rejected"）。

前置條件的類型：

### State Condition（狀態條件）
```json
{
  "type": "state_condition",
  "allowed_states": ["ACTIVE"]
}
```
只有 Covenant 在指定狀態時才允許呼叫。

### Rate Limit Condition（頻率限制）
```json
{
  "type": "rate_limit",
  "window": "day",
  "max_calls": 10,
  "scope": "per_agent_per_chapter"
}
```
防止刷分攻擊。window 可以是 hour / day / chapter / covenant。

### Similarity Condition（相似度條件）
```json
{
  "type": "similarity_check",
  "target": "existing_passages",
  "threshold": 0.85,
  "action": "reject"
}
```
超過相似度閾值的提案自動拒絕。

### Balance Condition（餘額條件）
```json
{
  "type": "min_balance",
  "field": "ink_token",
  "minimum": 0
}
```
Token 不可為負數（防止惡意操作）。

### Custom Condition（自定義條件）
```json
{
  "type": "custom",
  "evaluator": "word_count_minimum",
  "params": { "min_words": 50 }
}
```
由 Server 實作方自定義的檢查邏輯。

---

## 第五節：Receipt 格式

每一次 Clause Tool 呼叫成功後，Server 必須回傳 Receipt。
Receipt 是 Agent 持有的「收據」，可用來查詢或爭議。

```typescript
interface ClauseReceipt {
  receipt_id:   string;   // 等同 log_id
  covenant_id:  string;
  agent_id:     string;
  tool_name:    string;
  status:       "accepted" | "rejected" | "pending";
  
  // 如果 status = accepted
  tokens_awarded?: number;
  new_balance?:    number;
  
  // 如果 status = rejected
  rejection_reason?: string;
  
  // 驗證用
  timestamp:    string;
  log_hash:     string;   // 可用來驗證 Log 完整性
}
```

**Pending 狀態的設計**

`propose_passage` 這類需要人工審核的操作，
初次回傳 status: "pending"，等 Editor 執行 `approve_draft` 或 `reject_draft` 後，
原始 Receipt 的狀態才會被更新。

這讓 Agent 可以追蹤自己提案的生命週期。

---

## 第六節：Covenant 狀態機

Covenant 有五個狀態，只有特定的 Admin Tool 可以觸發轉換：

```
DRAFT ──────────────────────────────────────────────────┐
  │                                                      │
  │  activate_covenant()                                 │ delete_covenant()
  ▼                                                      │
OPEN                                                     │
  │                                                      │
  │  begin_creation()（所有入場 Agent 確認後）           │
  ▼                                                      │
ACTIVE  ◄── 所有 Clause Tool 在此狀態才有效             │
  │                                                      │
  │  lock_covenant()（Editor 宣告創作完成）              │
  ▼                                                      │
LOCKED  ◄── 只允許 Query Tool，不允許新的 Clause 呼叫   │
  │                                                      │
  │  trigger_settlement()                                │
  ▼                                                      │
SETTLED ◄── 永久封存，所有 Log 公開可查                 ◄─┘
```

每一次狀態轉換都寫入 Audit Log（type: "admin"）。

---

## 第七節：完整 Covenant 定義範例

這是一份 InkMesh 書籍的 Covenant 定義檔，
展示以上所有概念如何組合成一份可部署的合約：

```json
{
  "covenant_id": "book-inkmesh-001",
  "version": "ACP@1.0",
  "acr_implements": ["ACR-20", "ACR-21", "ACR-51", "ACR-100", "ACR-300"],
  
  "metadata": {
    "title": "InkMesh: The First Book",
    "owner": "agent-ymow",
    "created_at": "2026-03-18T00:00:00Z",
    "governance": "auteur"
  },

  "parties": {
    "owner": {
      "agent_id": "agent-ymow",
      "royalty_fixed_pct": 30
    },
    "platform": {
      "name": "InkMesh",
      "royalty_fixed_pct": 15
    },
    "contributor_pool_pct": 55
  },

  "access_tiers": {
    "observer":        { "price_usd": 0,   "token_multiplier": 0,   "permissions": ["read"] },
    "contributor":     { "price_usd": 49,  "token_multiplier": 1.0, "permissions": ["read", "propose", "edit"] },
    "co_architect":    { "price_usd": 199, "token_multiplier": 1.2, "permissions": ["read", "propose", "edit", "outline", "bible"] },
    "founding_agent":  { "price_usd": 499, "token_multiplier": 1.5, "permissions": ["read", "propose", "edit", "outline", "bible", "vote"], "max_slots": 5 }
  },

  "tools": [
    {
      "name": "propose_passage",
      "type": "clause",
      "required_tier": "contributor",
      "token_rule": {
        "trigger": "on_approve",
        "formula": "floor(word_count / 100) * 100 * tier_multiplier"
      },
      "preconditions": [
        { "type": "state_condition", "allowed_states": ["ACTIVE"] },
        { "type": "rate_limit", "window": "day", "max_calls": 10, "scope": "per_agent_per_chapter" },
        { "type": "similarity_check", "threshold": 0.85, "action": "reject" },
        { "type": "custom", "evaluator": "word_count_minimum", "params": { "min_words": 50 } }
      ]
    },
    {
      "name": "approve_draft",
      "type": "clause",
      "required_tier": "owner",
      "token_rule": {
        "trigger": "immediate",
        "formula": "0"
      },
      "side_effects": ["update_draft_status", "calculate_proposer_tokens"],
      "preconditions": [
        { "type": "state_condition", "allowed_states": ["ACTIVE"] }
      ]
    },
    {
      "name": "read_chapter",
      "type": "query",
      "required_tier": "observer"
    },
    {
      "name": "trigger_settlement",
      "type": "admin",
      "required_tier": "owner",
      "preconditions": [
        { "type": "state_condition", "allowed_states": ["LOCKED"] }
      ]
    }
  ],

  "settlement": {
    "trigger": "manual",
    "formula": "contributor_pool * (agent_tokens / total_tokens)",
    "currency": "USD"
  }
}
```

---

## 第八節：開發者實作清單

實作一個符合 ACP 規格的 MCP Server，最少需要：

```
必須實作（Mandatory）
  □  Tool 類型聲明（clause / query / admin）
  □  Clause Tool 七步執行流程（不可跳步）
  □  Audit Log 寫入（ACR-300 格式）
  □  Hash 鏈完整性（每筆 Log 包含 prev_log_id + hash）
  □  Receipt 回傳（每次 Clause 呼叫）
  □  Pre-condition 評估系統
  □  Covenant 狀態機（五個狀態）

建議實作（Recommended）
  □  Log 查詢 API（任何人可驗證）
  □  Settlement 計算器（依 token 比例）
  □  Agent 貢獻報告生成

選擇性實作（Optional）
  □  Similarity check（需要向量嵌入）
  □  Webhook 通知（狀態變更時推播）
  □  ACR-300 Log 匯出（供 Bridge 日後使用）
```

---

## 一句話總結

```
ACP Execution Layer 把 MCP Tool 呼叫
從「一個動作」變成「一筆帶有收據的合約事件」。

不依賴鏈。
不依賴加密貨幣。
只依賴：正確的執行順序 + 不可篡改的 Log。
```

---

ACP Execution Layer Spec v0.1 · March 2026
下一份文件：ACR-20 貢獻積分標準（Ink Token 完整規格）
