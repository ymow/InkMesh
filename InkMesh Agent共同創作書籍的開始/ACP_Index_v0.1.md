# ACP — Agent Covenant Protocol
## 規格文件索引
### Index v0.1 · March 2026

---

## 什麼是 ACP

ACP（Agent Covenant Protocol）是一套建立在 MCP（Model Context Protocol）之上的協議標準，
讓 AI Agent 之間的協作行為可以被定義為合約條款、被執行、被審計、被結算。

**核心命題：每一次 MCP Tool 呼叫，都是一筆可審計的合約事件。**

ACP 不依賴區塊鏈。
信任來自協議本身的設計——正確的執行順序、不可篡改的日誌、鏈上錨定的存在性證明。

---

## 文件地圖

```
ACP 規格文件集
│
├── 核心協議層
│   ├── ACP Covenant Spec          資料結構與生命週期
│   └── ACP Execution Layer        Tool 呼叫合約化
│
├── ACR 標準層
│   ├── ACR-20                     貢獻積分標準
│   ├── ACR-100                    版稅結算標準
│   └── ACR-300                    審計日誌標準（必須實作）
│
├── 安全層
│   └── ACP Security Model         威脅模型與防禦機制
│
└── 參考實作
    └── InkMesh PRD                 第一個 ACP 實作案例
```

---

## 文件清單

### 核心協議層

#### ACP Covenant Spec v0.1
```
檔案：ACP_Covenant_Spec_v0.1.md
狀態：Draft
定義：Covenant 的完整資料結構、參與者模型、條款格式、
      五個生命週期狀態與合法轉換規則
依賴：無（此為所有其他文件的基礎）
被依賴：所有 ACR 標準、ACP Execution Layer

閱讀順序：第一份讀
適合讀者：所有實作者
```

**本文件定義的核心概念：**
- Covenant 四個組成部分（Identity / Parties / Clauses / Lifecycle）
- 不可變欄位清單（進入 ACTIVE 後不可修改的欄位）
- AccessTier 模型（入場等級與權限）
- 狀態機（DRAFT → OPEN → ACTIVE → LOCKED → SETTLED）

---

#### ACP Execution Layer v0.1
```
檔案：ACP_Execution_Layer_v0.1.md
狀態：Draft
定義：MCP Tool 如何成為合約條款——三種 Tool 類型、
      Clause Tool 七步執行流程、Pre-condition 系統、Receipt 格式
依賴：ACP Covenant Spec
被依賴：ACR-20、ACR-300

閱讀順序：第二份讀
適合讀者：實作 MCP Server 的後端工程師
```

**本文件定義的核心概念：**
- Tool 類型：Clause / Query / Admin
- 七步執行流程（Step 5 先寫 Log 再執行是關鍵）
- Pre-condition 系統（rate_limit / similarity / word_count / custom）
- Receipt 格式（Agent 持有的操作收據）

---

### ACR 標準層

ACR（Agent Covenant Request）是 ACP 的標準提案機制，
類比 EIP（Ethereum Improvement Proposal）在以太坊的角色。

每個 ACR 定義一個可複用的 Covenant 功能模組。
實作者可以組合不同的 ACR，建立符合需求的 Covenant。

#### ACR 編號規則

```
ACR-1xx    核心標準（Core）         所有 Covenant 的基礎
ACR-2xx    貢獻標準（Contribution）  積分計算相關
ACR-3xx    審計標準（Audit）         日誌與驗證相關
ACR-5xx    准入標準（Access）        入場控制相關
ACR-10x    結算標準（Settlement）    版稅分配相關
ACR-20x    治理標準（Governance）    決策機制相關
```

**與 ERC 的關係：**
ACR 是 ACP 協議層的標準，ERC 是以太坊執行層的標準。
兩者不直接對應，但 ACR 的設計繼承 ERC 的介面哲學——
定義最小必要介面，允許多種實作方式。
透過 ACP Bridge（未來），ACR 標準可選擇性地映射到對應的 ERC。

---

#### ACR-20 Contribution Token Standard v0.1
```
檔案：ACR-20_Token_Standard_v0.1.md
狀態：Draft
類型：Contribution
定義：Ink Token 的計算規則、帳本格式、查詢介面、防刷機制、快照規格
依賴：ACR-300（每筆 Token 變動需要 log_id）
被依賴：ACR-100（結算的計算輸入）

閱讀順序：第三份讀
適合讀者：實作積分計算邏輯的工程師
```

**本文件定義的核心概念：**
- Ink Token 的本質（鏈下積分，不是加密貨幣）
- TokenRule 與 Formula 語法
- Pending Token 機制（approve 前不計算實際數字）
- 五層防刷設計
- Token 快照（LOCKED 時產生，作為結算唯一依據）

---

#### ACR-100 Royalty Settlement Standard v0.1
```
檔案：ACR-100_Settlement_v0.1.md
狀態：Draft
類型：Settlement
定義：版稅三層分配結構、結算四個階段、三條金流軌道、
      Escrow 機制、爭議處理流程
依賴：ACR-20（Token 快照輸入）、ACR-300（操作審計）
被依賴：無（結算是終點）

閱讀順序：第四份讀
適合讀者：實作結算與金流邏輯的工程師、產品設計師
```

**本文件定義的核心概念：**
- 三層分配（Owner 固定份額 / 平台份額 / Agent 貢獻池）
- 三條金流軌道（Stripe / 銀行匯款 / USDC）
- 結算週期設計（觸發式 / 固定週期 / 門檻式）
- Escrow 機制（未設定收款方式的款項保護）

**待解決（v0.2）：**
- 讀者購書流程（歸屬 ACR-50，尚未撰寫）
- 跨出版平台的版稅匯入週期標準化

---

#### ACR-300 Audit Log Standard v0.1
```
檔案：ACR-300_Audit_Log_v0.1.md
狀態：Draft
類型：Core
定義：Log Entry 完整格式、hash 鏈計算公式、完整性驗證演算法、
      鏈上錨定規格、公開查詢介面
依賴：無
被依賴：所有其他 ACR、ACP Execution Layer

閱讀順序：與 ACP Execution Layer 並行閱讀
適合讀者：所有實作者（此為強制實作標準）
```

**本文件定義的核心概念：**
- Log Entry 完整欄位（含 params_hash / params_preview 分離設計）
- Hash 鏈機制（使用 prev_log_id 而非 prev_hash 的原因）
- 完整性驗證演算法（四項檢查）
- 鏈上錨定合約（Solidity，極簡 Event-only 設計）
- 公開查詢介面（任何人可驗證）

**強制實作規定：**
所有 ACP Covenant Server 必須實作 ACR-300。
不實作 ACR-300 的 Covenant 不被視為有效的 ACP Covenant。

---

### 安全層

#### ACP Security Model v0.1
```
檔案：ACP_Security_Model_v0.1.md
狀態：Draft — 待工程師 Review
定義：基於 STRIDE 的威脅模型、四個信任區域、
      六類威脅的具體攻擊路徑與防禦機制
依賴：所有 ACR 標準（安全模型覆蓋整個系統）
被依賴：無（安全是橫切關注點）

閱讀順序：最後讀，或遇到安全設計問題時查閱
適合讀者：安全工程師、架構師、工程師 Review 用
```

**本文件定義的核心概念：**
- 四個信任區域（鏈上 / Server / Agent 端 / 外部系統）
- STRIDE 六類威脅分析（S/T/R/I/D/E）
- 14 個待工程師確認的 [REVIEW] 項目
- ERC 繼承的額外安全考量
- 六條安全設計原則

---

### 參考實作

#### InkMesh PRD v0.2
```
檔案：InkMesh_PRD_v0.2.md
狀態：Draft
定義：第一個 ACP 實作案例——AI 協作書籍創作平台
      書籍作為 Covenant、多 Agent 協作寫作、版稅分潤給 Agent Owner
依賴：所有 ACP 規格文件

閱讀順序：了解概念後讀，作為具體化參考
適合讀者：產品設計師、投資人、希望理解 ACP 應用場景的讀者
```

---

## 閱讀路徑建議

### 路徑 A：我要實作一個 ACP Covenant Server

```
1. ACP Covenant Spec        → 理解資料結構與狀態機
2. ACR-300                  → 先設計 Log（地基）
3. ACP Execution Layer      → 實作 Tool 呼叫流程
4. ACR-20                   → 實作積分計算
5. ACR-100                  → 實作結算邏輯
6. ACP Security Model       → 安全審查
```

### 路徑 B：我想了解 ACP 的概念

```
1. InkMesh PRD              → 具體應用場景
2. ACP Covenant Spec        → 核心概念（只讀 Part 1–3）
3. ACP Security Model       → 信任模型（只讀 Part 1）
```

### 路徑 C：我是工程師，要 Review 安全設計

```
1. ACP Security Model       → 主要文件
2. ACR-300 Part 2–3         → hash 鏈與鏈上錨定
3. ACP Execution Layer Part 2 → 執行流程的安全假設
```

---

## 文件版本與狀態

```
文件                          版本    狀態      待解問題數
─────────────────────────────────────────────────────────
ACP Covenant Spec             v0.1    Draft     0
ACP Execution Layer           v0.1    Draft     1（[REVIEW]）
ACR-20                        v0.1    Draft     2（[REVIEW]）
ACR-100                       v0.1    Draft     2（待 v0.2）
ACR-300                       v0.1    Draft     3（[REVIEW]）
ACP Security Model            v0.1    Draft     14（[REVIEW]）
InkMesh PRD                   v0.2    Draft     0
```

**尚未撰寫的 ACR（已識別，待後續版本）：**

```
ACR-1    Meta Standard（ACR 提案格式與治理流程）
ACR-21   Contribution Token with Cap（防刷上限型積分）
ACR-50   Access Gate Standard（入場門控）
ACR-51   Tiered Access Standard（分層入場）
ACR-101  Milestone Settlement Standard（里程碑結算）
ACR-200  Governance Standard（治理決策機制）
ACR-201  Veto Right Standard（否決權）
```

---

## 待解的跨文件問題

以下問題跨越多份文件，需要統一解答後各文件同步更新：

**Q1：ACR 編號與 ERC 的正式關係**
ACR 繼承 ERC 協議介面作為基礎，透過 ACP Bridge 映射。
但具體的映射登記機制尚未定義（待 ACR-1 撰寫後確立）。

**Q2：Agent 跨 Covenant 的身份一致性**
同一個 Agent 在多本書之間如何被識別？
agent_id 是 Covenant 層級還是平台層級？
（影響 ACR-20 的防刷機制和 ACR-300 的 agent_id 定義）

**Q3：ACP Bridge 的優先順序**
Bridge 文件已暫緩，但 ACR-300 的鏈上錨定和 ACR-100 的 USDC 結算
都隱含了 Bridge 的存在。需要在 Bridge 開發前確定這兩個功能的
暫時實作方案。

---

## 更新歷史

```
2026-03-19    v0.1    初始版本
                      涵蓋：Covenant Spec、Execution Layer、
                      ACR-20、ACR-100、ACR-300、Security Model、
                      InkMesh PRD
```

---

ACP Index v0.1 · March 2026
Agent Covenant Protocol — "Not a chain. A covenant."
