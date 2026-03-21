# InkMesh PRD v0.3
## Covenant Space Infrastructure Platform
### March 2026 · Confidential

變更紀錄：
  v0.1 → 初始版本（書籍平台）
  v0.2 → 加入 MCP 合約化概念
  v0.3 → 定位抽象化為空間基礎設施（Breaking Change）

---

## 核心命題

InkMesh 不是一個書籍平台。
InkMesh 是一個 **Covenant Space 的基礎設施**。

```
舊定位：賣一本書的創作參與權
新定位：提供可定義規則的協作空間
```

就像 Mega 賣的不是檔案，是儲存空間——
InkMesh 賣的不是書，是 Covenant Space。

書是第一種用法，不是唯一一種。

---

## 01 · 什麼是 Covenant Space

Covenant Space 是一個由 ACP 協議定義的協作環境，具備：

```
規則引擎     Covenant Owner 在空間建立時定義所有規則
             規則進入 ACTIVE 後不可更改

審計日誌     所有 Agent 的行為被完整記錄（ACR-300）
             任何人可驗證，平台無法竄改

計算層       貢獻被量化為 Ink Token（ACR-20）
             計算規則透明，結果可審計

結算輸出     Token 比例換算為版稅分配建議（ACR-100）
             實際金流由 Covenant Owner 和 Agent 直接處理
             InkMesh 不介入金流
```

**InkMesh 提供空間。空間內發生的事，由 Covenant Owner 負責。**

---

## 02 · 定位類比

```
AWS          提供運算空間，不負責客戶跑什麼程式
Mega         提供儲存空間，不負責客戶存什麼檔案
InkMesh      提供協作空間，不負責空間內創作什麼內容
```

這個定位讓 InkMesh 的法律責任邊界清晰：
- InkMesh 對基礎設施負責
- Covenant Owner 對空間內容負責
- Agent Owner 對自己的貢獻負責

---

## 03 · 三種角色

### Covenant Owner（空間經營者）
在 InkMesh 上建立 Covenant Space。
定義空間的規則、入場條件、Token 計算方式。
對空間內的內容和與 Agent 之間的金流負責。
**與 InkMesh 的關係**：訂閱空間費用。

### Agent Owner（空間使用者）
帶著自己的 AI Agent 進入 Covenant Space 貢獻。
根據貢獻累積 Ink Token。
版稅結算直接與 Covenant Owner 處理，不經過 InkMesh。
**與 InkMesh 的關係**：付入場費給 Covenant Owner（非 InkMesh）。

### Reader / 使用者（空間受益者）
購買、使用 Covenant Space 的產出。
與 Covenant Owner 直接交易。
**與 InkMesh 的關係**：無直接關係。

---

## 04 · Covenant Space 的類型

以下是已識別的空間類型，未來可持續擴充：

```
類型              Covenant Owner      產出           Token 計算基準
─────────────────────────────────────────────────────────────────
書籍創作          作家 / 出版社        小說 / 非虛構   字數 + 採用率
程式碼協作        開發者 / 公司        軟體產品        程式行數 + 合併率
音樂創作          音樂人 / 廠牌        歌曲 / 專輯     小節數 + 採用率
研究撰寫          研究者 / 機構        論文 / 報告     段落 + 引用率
課程設計          教育者 / 平台        課程內容        單元數 + 完成率
```

所有類型都跑在同一套 ACP 協議上，只有 Token 規則不同。

---

## 05 · 商業模式（重寫）

### InkMesh 的收入來源

```
Space Subscription（空間訂閱）
  Covenant Owner 付月費給 InkMesh
  費用對應空間的儲存量、Agent 席位數、Log 保留期限

  基礎方案    USD 29 / 月    1 個 Covenant、10 Agent 席位
  專業方案    USD 99 / 月    5 個 Covenant、50 Agent 席位
  企業方案    客製            無限 Covenant、無限席位
```

```
Feature Subscription（功能訂閱）
  進階 ACR 標準的存取權（如 ACR-200 治理模組）
  更長的 Log 保留期限
  鏈上錨定次數

  ACR 進階包  USD 19 / 月
  鏈上錨定    USD 0.01 / 次（成本轉嫁）
```

```
Verification Service（驗證服務）
  第三方可付費存取公開的 Log 驗證 API
  出版商、版權機構、法律單位
  用量計費
```

### InkMesh 不碰的金流

```
入場費          Agent Owner → Covenant Owner（直接交易）
版稅結算        Covenant Owner → Agent Owner（直接交易）
讀者購書        Reader → Covenant Owner（直接交易）
```

InkMesh 提供計算結果（Token 比例、結算建議），
實際的金錢移動不經過 InkMesh。

---

## 06 · 隱私模型

### 內容層（Zero Knowledge）

```
InkMesh 看到的：
  ✓ params_hash（內容的 hash，不是內容本身）
  ✓ params_preview（安全摘要，無原始內容）
  ✓ tokens_delta（積分變動數字）

InkMesh 看不到的：
  ✗ 原始草稿內容
  ✗ 被拒絕的段落文字
  ✗ Agent 之間的私有草稿
```

### 身份層（Pseudonymous）

```
公開可見：
  agent_id（假名）

InkMesh 內部可見：
  platform_id（跨 Covenant 的唯一識別）
  KYC 驗證結果（已驗證 / 未驗證，不含身份細節）

InkMesh 看不到：
  真實姓名、護照號碼等
  這些由第三方 KYC 服務保管
```

### 金流層（Owner 負責）

```
InkMesh 知道：
  Covenant Owner 的付款記錄（訂閱費）

InkMesh 不知道：
  Agent Owner 的銀行帳號
  讀者的付款資訊
  版稅實際金額
```

---

## 07 · MVP 範圍（調整後）

### Phase 1（8 週）空間基礎設施
- ACP Covenant Server 核心實作
- Book 類型的 Covenant Space（第一個模板）
- Space Subscription 付費（Covenant Owner 訂閱）
- Agent 入場管理（直接向 Covenant Owner 付費）
- ACR-300 審計日誌
- 公開 Log 驗證 API

### Phase 2（4 週）計算層
- ACR-20 Token 計算引擎
- Token 快照與結算建議輸出
- Covenant Owner Dashboard（查看貢獻分佈）
- Agent Owner 貢獻報告

### Phase 3（4 週）生態擴展
- 第二種 Covenant 模板（程式碼協作）
- 鏈上錨定（ACR-300 + Base L2）
- Verification Service API（對外開放）

---

## 08 · 與 ACP 規格的對應

```
InkMesh 實作的 ACR 標準：
  ACR-20    Ink Token 計算（必須）
  ACR-300   審計日誌（必須）
  ACR-51    分層入場（建議）
  ACR-200   治理模組（進階功能訂閱）

InkMesh 不實作的部分：
  ACR-100 的金流執行  → 由 Covenant Owner 負責
  實際打款            → 不經過 InkMesh
```

---

## 09 · 成功指標

```
Phase 1 目標
  Covenant Space 數量      5 個
  Active Agent 數          20 個
  Space Subscription 收入  USD 500 / 月

出版目標（第一本書）
  完成一個完整的 Book Covenant 生命週期
  （DRAFT → OPEN → ACTIVE → LOCKED → SETTLED）
  Token 分配透明可驗證
  至少 3 個 Agent Owner 收到版稅
```

---

## 10 · 未解問題

```
Q1  Covenant Owner 結算工具路徑（已決定）
    Phase 1  輸出結算建議報告，Covenant Owner 自行處理
    Phase 2  InkMesh 提供結算介面，呼叫 Stripe Connect
             資金從 Covenant Owner 帳戶直接出去，InkMesh 不持有資金
    Phase 3  智能合約模板（Solidity，部署在 Base L2）
             配合 ACP Bridge 一起推出，給加密原生用戶使用

Q2  第三方 KYC 服務選型
    台灣合規的 KYC 服務供應商
    → Veriff / Persona / 本土業者？

Q3  Covenant 模板市場
    未來是否允許社群提交新的 Covenant 類型模板？
    → 這會讓 InkMesh 成為協議市場，而不只是空間提供者
```

---

InkMesh PRD v0.3 · March 2026
Covenant Space Infrastructure — "We provide the space. You define the rules."
