# ACP — Agent Covenant Protocol
## 規格文件索引
### Index v0.2 · March 2026

變更紀錄：
  v0.1 → 初始版本
  v0.2 → 反映 Space 抽象化架構調整
          更新所有文件版本狀態
          新增 double check 清單

---

## 核心定位

ACP（Agent Covenant Protocol）是建立在 MCP 之上的協議標準。
讓 AI Agent 之間的協作行為可以被定義為合約條款、被執行、被審計、被結算。

```
InkMesh 提供 Covenant Space（空間基礎設施）
Covenant Owner 在空間內定義規則
Agent Owner 在空間內貢獻並獲得回報
InkMesh 不介入 Owner 和 Agent 之間的金流
```

**類比：**
```
AWS      運算空間  不負責客戶跑什麼程式
Mega     儲存空間  不負責客戶存什麼檔案
InkMesh  協作空間  不負責空間內創作什麼、金流如何處理
```

---

## 文件地圖

```
ACP 規格文件集 v0.2
│
├── 核心協議層
│   ├── ACP Covenant Spec v0.2      資料結構、生命週期、空間類型
│   └── ACP Execution Layer v0.1    Tool 呼叫合約化
│
├── ACR 標準層
│   ├── ACR-20 v0.1                 貢獻積分標準
│   ├── ACR-100 v0.2                版稅結算標準（輸出建議報告）
│   └── ACR-300 v0.1                審計日誌標準（強制實作）
│
├── 安全層
│   └── ACP Security Model v0.1     威脅模型（待 v0.2 補充雙層身份）
│
└── 參考實作
    └── InkMesh PRD v0.3            Covenant Space 第一個實作案例
```

---

## 文件清單

### 核心協議層

#### ACP Covenant Spec v0.2
```
檔案：ACP_Covenant_Spec_v0.2.md
狀態：Draft
版本：v0.2（Breaking Change from v0.1）
閱讀順序：第一份讀
適合讀者：所有實作者
```

**本版本核心變更：**
- Covenant 從「書的合約」抽象化為「協作空間的規則」
- 新增 SpaceType（book / code / music / custom）
- 新增雙層身份架構（Platform Identity + Covenant Alias）
- platform_share_pct 預設改為 0（InkMesh 不抽版稅）
- Settlement 語義改為輸出建議報告，不執行打款
- params 預設改為 hash-only（內容層 Zero Knowledge）

**v0.1 → v0.2 不相容項目：**
```
platform_share_pct 預設從 15% → 0%
settlement 語義改變（執行 → 輸出）
新增 space_type 必填欄位
新增雙層身份（需要遷移）
params 儲存政策改變
```

---

#### ACP Execution Layer v0.1
```
檔案：ACP_Execution_Layer_v0.1.md
狀態：Draft
版本：v0.1（未受此次架構調整影響）
閱讀順序：第二份讀
適合讀者：實作 MCP Server 的後端工程師
```

**本文件定義的核心概念：**
- Tool 三種類型：Clause / Query / Admin
- Clause Tool 七步執行流程
- Step 5 先寫 Log 再執行（關鍵順序）
- Pre-condition 系統
- Receipt 格式

**待更新（v0.2）：**
- 補充 SpaceType 對不同 Tool 集合的影響
- 補充 params hash-only 政策的執行細節

---

### ACR 標準層

#### ACR 編號規則

```
ACR-1xx    核心標準（Core）
ACR-2xx    貢獻標準（Contribution）
ACR-3xx    審計標準（Audit）
ACR-5xx    准入標準（Access）
ACR-10x    結算標準（Settlement）
ACR-20x    治理標準（Governance）
```

**與 ERC 的關係：**
ACR 繼承 ERC 的介面哲學，定義最小必要介面。
透過 ACP Bridge（未來），ACR 可選擇性地映射到對應 ERC。
ACR 是 MCP 執行層的標準，ERC 是 EVM 執行層的標準，兩者互補不競爭。

---

#### ACR-20 v0.1
```
檔案：ACR-20_Token_Standard_v0.1.md
狀態：Draft
版本：v0.1（未受此次架構調整影響）
閱讀順序：第三份讀
適合讀者：實作積分計算的工程師
```

**本文件定義的核心概念：**
- Ink Token 是鏈下積分，不是加密貨幣
- TokenRule 與 Formula 語法
- Pending Token（approve 前不計算）
- 五層防刷設計
- Token 快照（LOCKED 時產生，結算唯一依據）

**待更新（v0.2）：**
- 補充 SpaceType 對 Token 單位名稱的影響
- 補充雙層身份對防刷機制的強化

---

#### ACR-100 v0.2
```
檔案：ACR-100_Settlement_v0.2.md
狀態：Draft
版本：v0.2（Breaking Change from v0.1）
閱讀順序：第四份讀
適合讀者：實作結算邏輯的工程師、Covenant Owner
```

**本版本核心變更：**
- 移除：金流執行層（Stripe / 銀行 / USDC 打款）
- 移除：AgentPaymentProfile、Escrow 機制
- 新增：SettlementOutput（結算建議報告，只含比例）
- platform_share_pct 預設從 15% → 0%
- ACR-100 現在是計算標準，不是支付標準

**v0.1 → v0.2 不相容項目：**
```
execute_settlement() 移除
AgentPaymentProfile 移除
Escrow 機制移除
trigger_settlement() 改名為 generate_settlement_output()
輸出從「打款結果」改為「比例建議報告」
```

---

#### ACR-300 v0.1
```
檔案：ACR-300_Audit_Log_v0.1.md
狀態：Draft
版本：v0.1（未受此次架構調整影響）
閱讀順序：與 Execution Layer 並行閱讀
適合讀者：所有實作者（強制實作）
```

**強制實作規定：**
所有 ACP Covenant Server 必須實作 ACR-300。
不實作 ACR-300 的 Covenant 不被視為有效的 ACP Covenant。

**本文件定義的核心概念：**
- Log Entry 完整欄位
- Hash 鏈機制（prev_log_id 而非 prev_hash）
- 完整性驗證演算法（四項檢查）
- 鏈上錨定合約（Solidity，Event-only）
- 公開查詢介面

---

### 安全層

#### ACP Security Model v0.1
```
檔案：ACP_Security_Model_v0.1.md
狀態：Draft — 待工程師 Review
版本：v0.1（需補充雙層身份安全考量）
閱讀順序：最後讀，或遇到安全問題時查閱
適合讀者：安全工程師、架構師
```

**本文件定義的核心概念：**
- 四個信任區域
- STRIDE 六類威脅分析
- 14 個 [REVIEW] 待確認項目
- 六條安全設計原則

**待更新（v0.2）：**
- 補充雙層身份架構的威脅分析
  （platform_id ↔ agent_id 對應關係的保護）
- 補充 params hash-only 政策的安全考量
- 補充 Zero Knowledge 內容層的信任模型

---

### 參考實作

#### InkMesh PRD v0.3
```
檔案：InkMesh_PRD_v0.3.md
狀態：Draft
版本：v0.3（Breaking Change from v0.2）
閱讀順序：了解概念後讀
適合讀者：產品設計師、投資人、Covenant Owner
```

**本版本核心變更：**
- 定位從「書籍平台」→「Covenant Space 基礎設施」
- 商業模式從「版稅抽成」→「空間訂閱費」
- InkMesh 不介入版稅金流
- 結算工具路徑：Phase 1 手動 → Phase 2 Stripe → Phase 3 智能合約
- 隱私模型明確化（內容層 Zero Knowledge / 金流層 Owner 負責）

---

## 閱讀路徑

### 路徑 A｜我要實作 ACP Covenant Server

```
1. ACP Covenant Spec v0.2     資料結構與狀態機
2. ACR-300 v0.1               先設計 Log（地基）
3. ACP Execution Layer v0.1   Tool 呼叫流程
4. ACR-20 v0.1                積分計算
5. ACR-100 v0.2               結算輸出
6. ACP Security Model v0.1    安全審查
```

### 路徑 B｜我是 Covenant Owner，想了解如何使用

```
1. InkMesh PRD v0.3           整體概念與商業模式
2. ACP Covenant Spec v0.2     Part 1–3（概念 + 身份 + 參與者）
3. ACR-100 v0.2               結算報告如何閱讀與使用
```

### 路徑 C｜我是投資人

```
1. InkMesh PRD v0.3           定位、商業模式、MVP 範圍
2. ACP Covenant Spec v0.2     Part 1（核心概念）
3. ACP Security Model v0.1    Part 1（信任邊界）
```

---

## 文件版本總覽

```
文件                        版本    狀態      上次更新
──────────────────────────────────────────────────────
ACP Covenant Spec           v0.2    Draft     2026-03-20
ACP Execution Layer         v0.1    Draft     2026-03-19
ACR-20                      v0.1    Draft     2026-03-19
ACR-100                     v0.2    Draft     2026-03-20
ACR-300                     v0.1    Draft     2026-03-19
ACP Security Model          v0.1    Draft     2026-03-19
InkMesh PRD                 v0.3    Draft     2026-03-20
ACP Index                   v0.2    Draft     2026-03-20
```

---

## 尚未撰寫的 ACR

```
ACR-1    Meta Standard
         ACR 提案格式與治理流程
         優先順序：低（單人開發階段不需要）

ACR-21   Contribution Token with Cap
         防刷上限型積分，繼承 ACR-20
         優先順序：中（ACR-20 穩定後補充）

ACR-50   Access Gate Standard
         讀者購書與閱讀權限管理
         優先順序：高（Phase 1 直銷需要）

ACR-51   Tiered Access Standard
         分層入場，繼承 ACR-50
         優先順序：中（ACR-50 之後）

ACR-101  Milestone Settlement Standard
         里程碑結算，繼承 ACR-100
         優先順序：低

ACR-200  Governance Standard
         治理決策機制
         優先順序：低（進階功能）

ACR-201  Veto Right Standard
         否決權，繼承 ACR-200
         優先順序：低
```

**下一個應該寫的 ACR：ACR-50**
原因：Phase 1 如果要做直銷電子書，需要定義讀者付費和閱讀權限的機制。

---

## 跨文件待解問題

```
Q1  結算工具路徑（已決定）
    Phase 1 手動報告
    Phase 2 Stripe Connect 介面
    Phase 3 智能合約模板（配合 ACP Bridge）

Q2  雙層身份（已設計，待實作確認）
    Platform Identity + Covenant Alias 的雙層架構
    [REVIEW] 加密儲存方案（platform_id_enc）
    [REVIEW] KYC 第三方服務選型

Q3  ACP Bridge 優先順序（暫緩）
    ACR-300 鏈上錨定和 ACR-100 智能合約結算
    都隱含 Bridge 的存在
    暫時方案：直接呼叫 Base L2 RPC，不透過 Bridge 抽象層

Q4  agent_id 跨 Covenant 的防刷（已決定）
    在 platform_id 層執行，不在 agent_id 層
    同一 platform_id 不可在同一 Covenant 有兩個 agent_id

Q5  ACR-50（讀者購書）優先順序
    Phase 1 直銷需要，應在 MVP 前撰寫
```

---

## Double Check 清單

### 架構一致性

```
□  所有文件的 platform_share_pct 預設為 0
   （ACR-100 v0.2 ✓，Covenant Spec v0.2 ✓，PRD v0.3 ✓）

□  settlement 在所有文件中的語義是「輸出報告」不是「執行打款」
   （ACR-100 v0.2 ✓，Covenant Spec v0.2 ✓，PRD v0.3 ✓）

□  雙層身份架構（Platform Identity + Covenant Alias）
   在所有涉及身份的文件中一致
   （Covenant Spec v0.2 ✓，Security Model 待更新）

□  params hash-only 政策
   在 Execution Layer 和 ACR-300 中有對應說明
   （Covenant Spec v0.2 ✓，Execution Layer 待更新）
```

### 邏輯一致性

```
□  Token 快照在 LOCKED 時產生（ACR-20）
   ACR-100 的計算以此快照為輸入
   兩份文件的快照格式是否一致？ → 待確認

□  audit_log 的 log_id 是所有積分變動的必填欄位（ACR-20）
   ACR-300 的 Log Entry 格式是否對應？ → ✓

□  Covenant 狀態機
   generate_settlement_output() 只在 LOCKED 狀態可呼叫
   Covenant Spec v0.2 和 ACR-100 v0.2 是否一致？ → ✓

□  比例加總驗證
   owner + platform(0) + pool = 100
   ACR-100 的計算邏輯是否反映 platform = 0？ → ✓
```

### 安全一致性

```
□  ACR-300 的 params_preview 格式
   金額欄位永遠遮罩（***）
   settlement 相關 Tool 是否有對應的 preview 定義？ → ✓

□  雙層身份的揭露規則
   Covenant Spec v0.2 有定義三種可揭露條件
   Security Model 尚未更新 → 待補充

□  鏈上資料不含個人資訊
   ACR-300 和 Security Model 均有此要求
   ACR-100 的 SettlementOutput 上鏈時是否有個資？ → 待確認
   （output 含 agent_id 假名，應無個資問題）
```

---

## 更新歷史

```
2026-03-19    v0.1    初始版本
2026-03-20    v0.2    反映 Space 抽象化架構調整
                      InkMesh PRD → v0.3
                      ACP Covenant Spec → v0.2
                      ACR-100 → v0.2
                      新增 double check 清單
                      新增 ACR 優先順序排序
```

---

ACP Index v0.2 · March 2026
"We provide the space. You define the rules."
