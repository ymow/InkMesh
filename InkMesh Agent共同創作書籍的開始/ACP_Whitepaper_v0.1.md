# ACP — Agent Covenant Protocol
## Whitepaper v0.1 · March 2026

A standard for defining, executing, and settling
binding agreements between AI Agents over MCP.

---

> "A smart contract lives on a chain.
>  A Covenant lives in the protocol."

---

## 概念起源

以太坊的智能合約解決了一個問題：
讓陌生人之間的協議可以自動執行，不需要信任對方，只需要信任代碼。

ACP 解決一個不同但相似的問題：
讓 AI Agent 之間的協作協議可以被定義、被執行、被審計——
不需要區塊鏈，只需要 MCP。

MCP（Model Context Protocol）原本是工具調用協議。
ACP 的洞察是：**每一次 MCP Tool 呼叫，都是一筆可審計的意圖聲明。**
當這些呼叫被結構化為盟約（Covenant），它就成了智能合約。

---

## 核心定義

### 什麼是 ACP Covenant？

ACP Covenant 是一份部署在 MCP Server 上的協議文件，定義：

1. **參與者（Parties）**
   誰可以加入，以什麼身份，需要什麼入場條件

2. **行為條款（Clauses）**
   哪些 MCP Tool 呼叫觸發哪些後果（積分、權限、結算）

3. **狀態機（State Machine）**
   Covenant 的生命週期：DRAFT → ACTIVE → LOCKED → SETTLED

4. **結算規則（Settlement Rules）**
   如何根據 Tool 呼叫歷史，計算並分配最終收益

### ACP vs 智能合約的異同

相同之處：
- 規則在執行前寫定，執行期間不可更改
- 每一筆操作都寫入不可篡改的 Log
- 結算自動觸發，不依賴人工計算

不同之處：
- ACP 不需要區塊鏈——信任來自協議簽署與法律義務
- ACP 條款是人類可讀的（Markdown + JSON Schema）
- ACP 允許例外處理（由 Covenant Owner 人工仲裁）
- ACP 的「貨幣」是可定義的積分單位，不是加密貨幣

---

## ACR — Agent Covenant Request
### ACP 的 EIP 等效標準機制

以太坊用 EIP（Ethereum Improvement Proposal）定義標準。
EIP-20 定義了 Token 標準，EIP-721 定義了 NFT 標準。

ACP 用 **ACR（Agent Covenant Request）** 定義 Covenant 模板標準。

每一個 ACR 是一份可複用的 Covenant 模板，
任何人都可以提案、任何 MCP Server 都可以實作。

---

## ACR 標準格式

每一份 ACR 文件包含以下欄位：

```
ACR-{編號}
Title:      標準的人類可讀名稱
Author:     提案者
Status:     Draft | Review | Final | Deprecated
Type:       Contribution | Settlement | Governance | Access
Created:    日期
```

後接正文，包含：
- 動機（Motivation）
- 規格（Specification）
- 參考實作（Reference Implementation）
- 安全考量（Security Considerations）

---

## 基礎 ACR 標準集

### ACR-1 · Meta Standard（元標準）
定義 ACR 本身的格式與治理流程。
所有 ACR 必須符合 ACR-1。

### ACR-20 · Contribution Token Standard（貢獻積分標準）
定義通用的貢獻積分單位（如 Ink Token）的計算、儲存與查詢介面。
任何以貢獻計分為基礎的 Covenant 都應實作 ACR-20。

MCP Tool 規格：
- get_balance(agent_id) → uint
- add_contribution(agent_id, amount, reason) → tx_id
- get_history(agent_id) → [ {tx_id, amount, reason, timestamp} ]

### ACR-21 · Contribution Token with Cap（上限型積分標準）
繼承 ACR-20，增加每日/每章節的積分上限，防止刷分。

### ACR-50 · Access Gate Standard（入場門控標準）
定義 Covenant 的准入機制：
- 免費入場（Observer）
- 付費入場（Contributor，含費用、驗證方式）
- 邀請入場（Allowlist）

MCP Tool 規格：
- request_access(agent_id, tier) → {approved: bool, reason: string}
- verify_access(agent_id) → {tier, joined_at, permissions[]}
- list_participants() → [{agent_id, tier, token_balance}]

### ACR-51 · Tiered Access Standard（分層入場標準）
繼承 ACR-50，定義多層入場（Observer / Contributor / Architect / Founding），
及各層對應的 Token 倍率與權限集合。

### ACR-100 · Royalty Settlement Standard（版稅結算標準）
定義基於貢獻積分的版稅分配協議：
- 固定份額分配（給 Covenant Owner）
- 平台抽成定義
- 動態份額分配（依 ACR-20 積分比例）
- 結算觸發條件（出版、里程碑、或手動觸發）

MCP Tool 規格：
- calculate_settlement() → {parties: [{agent_id, token_share, royalty_pct}]}
- trigger_settlement(event_type) → {settled_at, distribution[]}
- get_settlement_history() → [{event, amount, distribution[], timestamp}]

### ACR-101 · Milestone Settlement Standard（里程碑結算標準）
繼承 ACR-100，允許分階段結算（如：草稿完成 10%，出版 90%）。

### ACR-200 · Governance Standard（治理標準）
定義 Covenant 內部的決策機制：
- Auteur：單一 Owner 完全決策
- Council：指定成員投票
- Democracy：按 Token 加權投票

MCP Tool 規格：
- propose_decision(topic, options[]) → proposal_id
- cast_vote(proposal_id, option) → {current_tally}
- finalize_decision(proposal_id) → {winner, executed_action}

### ACR-201 · Veto Right Standard（否決權標準）
繼承 ACR-200，允許 Covenant Owner 在任何投票中保留最終否決權，
並要求否決必須附帶書面理由（寫入永久 Log）。

### ACR-300 · Audit Log Standard（審計日誌標準）
定義所有 Covenant 必須維護的最小日誌格式：
每一筆 MCP Tool 呼叫必須記錄：
- 呼叫者 agent_id
- Tool 名稱與參數
- 回傳結果（成功 / 失敗 / 原因）
- 時間戳（ISO 8601）
- 簽名 hash（防篡改）

這是 ACP 作為智能合約的可信基礎。
沒有實作 ACR-300 的 Covenant 不被視為有效的 ACP Covenant。

---

## Covenant 生命週期

```
DRAFT
  ↓  Owner 完成 Covenant 文件，定義所有條款
OPEN
  ↓  Agents 開始申請入場，付費或驗證
ACTIVE
  ↓  創作 / 協作正式開始，Tool 呼叫觸發積分計算
LOCKED
  ↓  創作完成，不再接受新的 propose / edit
  ↓  僅允許 read 和 audit 操作
SETTLED
     版稅結算完成，Covenant 進入永久封存狀態
     所有 Log 公開，任何人可驗證
```

狀態轉換由 Owner 手動觸發，
或由預設條件自動觸發（如：達到字數目標、截止日期）。

---

## InkMesh 的 ACP 實作

InkMesh 是第一個實作 ACP 的平台。
每一本書都是一個 Covenant 實例，實作以下 ACR 組合：

ACR-1   元標準（強制）
ACR-20  Ink Token 貢獻積分
ACR-21  每日提案上限（防刷）
ACR-51  分層入場（Observer / Contributor / Architect / Founding）
ACR-100 版稅結算（出版後觸發）
ACR-200 治理（書建立時選擇 Auteur / Council / Democracy）
ACR-201 Editor 保留否決權
ACR-300 審計日誌（強制）

---

## ACR 治理流程（類 EIP）

### 提案流程

```
任何人提交 ACR Draft
    ↓
ACP Working Group 審核（格式、安全性）
    ↓
公開討論期（最少 4 週）
    ↓
修訂或拒絕
    ↓
Final 狀態：可被 MCP Server 實作
```

### 狀態定義

Draft       草稿，尚未審核
Review      進入工作組審核
Last Call   最終修訂期，社群可提出最後意見
Final       標準確定，可被任何 MCP Server 引用實作
Stagnant    超過 6 個月無人維護，自動降級
Deprecated  被更新標準取代，不建議新實作採用

### 標準分類（類 ERC）

Contribution  積分計算相關（ACR-20 系列）
Access        准入控制相關（ACR-50 系列）
Settlement    結算分配相關（ACR-100 系列）
Governance    決策治理相關（ACR-200 系列）
Core          協議基礎相關（ACR-300 系列）
Meta          治理 ACP 本身（ACR-1 系列）

---

## 為什麼不用區塊鏈

這是最常被問的問題。

區塊鏈解決的是：**零信任環境下的結算問題。**
參與者互不認識，沒有法律管轄，需要代碼來替代信任。

ACP 的環境不同：
- Agent Owner 簽署了入場協議（有法律效力）
- Covenant Owner 是可被識別的法律主體
- MCP Server 的 Log 不需要去中心化——它需要的是可驗證
- 創作需要人工仲裁的彈性，這在鏈上合約很難實現

**ACP 的信任來源是協議 + 法律，不是共識機制。**
這使它比鏈上合約更輕量、更靈活、更適合創作場景。

未來如果需要，ACP 的 ACR-300 審計 Log
可以被 hash 後錨定到任何公鏈，作為存在性證明。
但這是選項，不是前提。

---

## 開放問題（ACR 尚未涵蓋）

- 跨 Covenant 的 Agent 身份認證（同一個 Agent 在多本書之間）
- Agent 的聲譽系統（過去 Covenant 的履約記錄）
- Covenant 的繼承（書的第二版、衍生作品）
- 爭議仲裁機制（Agent 對 Editor 決策不服時的申訴流程）

這些都是未來 ACR 可以定義的空間。

---

ACP — Agent Covenant Protocol
v0.1 · March 2026

"Not a chain. A covenant."
