# ACP Bridge
## MCP ↔ EIP 協議互通中台
### Architecture Spec v0.1 · March 2026

---

## 為什麼需要中台

EIP 花了十年建立的東西：
- 標準的 Token 介面（ERC-20、ERC-721）
- 可組合的合約模式
- 被全球開發者信任的規格格式
- 一套完整的提案治理流程

MCP 有的東西：
- 即時的 Agent 工具調用能力
- 彈性的人工仲裁空間
- 人類可讀的協議設計
- 快速迭代的執行層

這兩個世界現在是分開的。
ACP Bridge 是讓它們互通的中台。

---

## 核心定位

```
ACP Bridge 不是新的標準。
它是已存在標準之間的翻譯層。
```

就像 Chainlink 不替代以太坊，也不替代現實世界的資料——
它只做一件事：讓兩個世界可以說話。

ACP Bridge 做的事：
- 把 MCP Tool 呼叫翻譯成 EIP 相容的事件格式
- 把 EIP 合約狀態同步回 MCP Resource
- 讓 ACR 標準可以直接引用 ERC 標準，而不是重新定義

---

## 三層架構

```
┌─────────────────────────────────────────┐
│           EIP Layer（以太坊）            │
│  ERC-20 Token · ERC-721 NFT            │
│  EIP-712 Signature · EIP-1559 Gas      │
│  任何 L1 / L2（Base, Arbitrum...）      │
└──────────────────┬──────────────────────┘
                   │
                   │  ACP Bridge（中台）
                   │
┌──────────────────▼──────────────────────┐
│              Bridge Core                │
│                                         │
│  Event Normalizer   →  EIP Adapter      │
│  ACR Mapper         →  Chain Router     │
│  State Syncer       →  Proof Writer     │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│           MCP Layer（執行層）            │
│  Book MCP Server · Tool Calls          │
│  ACR-300 Audit Log · Agent Sessions    │
└─────────────────────────────────────────┘
```

---

## Bridge Core 四個模組

### 1. Event Normalizer（事件正規化器）

MCP Tool 呼叫的格式是自由的。
EIP 事件（Event）有嚴格的 ABI 定義。

Event Normalizer 負責把 MCP 呼叫轉換成標準事件格式：

```
MCP Tool 呼叫（原始）：
  tool: "approve_draft"
  params: { draft_id: "d-001", agent_id: "agent-A", word_count: 320 }
  result: { status: "ACCEPTED", tokens_awarded: 320 }

↓ Event Normalizer

ACP Standard Event：
  event: "ContributionSettled"
  version: "ACR-20@1.0"
  covenant_id: "book-001"
  agent_id: "agent-A"
  amount: 320
  reason: "approve_draft:d-001"
  timestamp: "2026-03-18T10:00:00Z"
  hash: "0xabc123..."
```

標準事件格式可以被任何下游系統消費——
不管是 EIP Adapter、資料庫、或第三方審計工具。

---

### 2. ACR Mapper（標準映射器）

ACR Mapper 的工作是：
**讓 ACR 標準直接引用 ERC 標準，而不是重新定義。**

映射表範例：

```
ACR-20（貢獻積分）
  ↕ 映射
ERC-20（同質化 Token）
  方向：ACR-20 的積分可選擇性地發行為 ERC-20 Token
  映射方法：1 Ink Token = 1 INK（鏈上）
  觸發時機：Covenant 進入 LOCKED 狀態時批次發行

ACR-51（分層入場）
  ↕ 映射
ERC-721（非同質化 Token）
  方向：入場憑證可發行為 NFT
  映射方法：每個入場等級對應不同 tokenURI metadata
  觸發時機：付費入場成功時 mint

ACR-100（版稅結算）
  ↕ 映射
ERC-20 transfer() + EIP-712 Permit
  方向：結算直接透過鏈上 transfer 執行
  映射方法：計算各方比例 → 呼叫合約分配
  觸發時機：Settlement trigger 事件

ACR-300（審計日誌）
  ↕ 映射
EIP-712（結構化資料簽名）
  方向：每個 epoch 的 Log hash 用 EIP-712 格式簽名後上鏈
  映射方法：calldata 寫入 L2
  觸發時機：每個章節完成時
```

ACR Mapper 讓 ACP 不需要重新發明 Token、NFT、或簽名標準。
它只需要定義映射關係。

---

### 3. Chain Router（鏈路由器）

不同的操作適合不同的鏈：

```
操作類型               建議鏈             原因
─────────────────────────────────────────────────────
審計 Log 錨定          Base / Arbitrum    L2，成本極低
入場憑證 NFT mint      Base               低 gas，成熟生態
Ink Token 發行         Base               同上
版稅結算 transfer      Polygon / Base     穩定幣友好
長期存檔               Ethereum L1        最高安全性，貴但值得
```

Chain Router 根據操作類型自動選擇最適合的鏈，
不需要 Agent Owner 或 Editor 手動選擇。

---

### 4. State Syncer（狀態同步器）

鏈上狀態需要反映回 MCP Resource，讓 Agent 可以讀取。

```
鏈上事件：INK Token mint（agent-A 獲得 320 INK）
    ↓ State Syncer
MCP Resource 更新：book://contributions
    { agent_id: "agent-A", onchain_balance: 320, verified: true }
```

State Syncer 維護雙向一致性：
- MCP → 鏈上：當 Covenant 執行時寫入鏈上
- 鏈上 → MCP：當鏈上確認後更新 MCP 狀態

這讓 Agent 的世界（MCP）和結算的世界（鏈上）保持同步，
不需要 Agent 自己理解區塊鏈。

---

## ACR 引用 EIP 的標準語法

有了 Bridge，ACR 文件可以直接引用 EIP，不需要重新定義：

```yaml
# ACR-20 貢獻積分標準（節錄）

eip_compatibility:
  - eip: ERC-20
    mapping: contribution_token
    optional: true          # 不強制鏈上化，但 Bridge 支援
    bridge_module: ACRMapper

settlement:
  eip: ERC-20
  method: transfer
  trigger: covenant_settled
  requires: ACR-100
```

這語法的意義：
ACR-20 不需要描述 ERC-20 是什麼——
它只需要說「我和 ERC-20 相容，透過 Bridge 的 ACRMapper 模組」。

任何實作 ACP Bridge 的平台都知道如何處理這個聲明。

---

## ACP Bridge 的開放策略

ACP Bridge 本身是開源的中間件。
任何 MCP Server 都可以掛載 ACP Bridge，獲得 EIP 互通能力。

```
平台自架 MCP Server
    + 掛載 ACP Bridge
    = 自動獲得：
        ✓ ERC-20 Ink Token 發行能力
        ✓ ERC-721 入場憑證 NFT
        ✓ 鏈上審計 Log 錨定
        ✓ 自動版稅結算
```

InkMesh 是第一個實作 ACP Bridge 的平台。
但任何人都可以用同樣的 Bridge 建立自己的協作平台——
寫程式碼協作、做音樂協作、做設計協作。

---

## 與現有 EIP 治理流程的接軌

ACP Bridge 不試圖進入 EIP 的治理流程——
那是以太坊生態系的事，不是 ACP 的事。

ACP Bridge 做的是：
1. 追蹤 EIP 的最終（Final）標準
2. 為每個 Final EIP 維護一個 ACR Mapper 模組
3. 當 EIP 有破壞性更新時，發布新版 ACR Mapper
4. 社群透過 ACR 治理流程決定是否採用新版 Mapper

這樣 ACP 可以永遠跟上 EIP 的進展，
但不依賴以太坊基金會的時間表。

---

## 實作路徑

### Phase 0（現在）
設計 ACR Mapper 的映射表規格
確認 ACR-20 ↔ ERC-20 的映射邏輯

### Phase 1（MVP 後）
實作 Event Normalizer
實作 ACR-300 Log → Base L2 錨定
最小化 Chain Router（只支援 Base）

### Phase 2
實作 ERC-20 Ink Token 發行
實作 ERC-721 入場憑證 NFT
State Syncer 雙向同步

### Phase 3
完整 Chain Router（多鏈支援）
開源 Bridge SDK
讓其他平台可以掛載

---

## 一句話定位

```
ACP Bridge：
讓 MCP 的每一次工具呼叫，
都可以在以太坊上被驗證。
```

不是替代 EIP。
不是重新發明 Token。
只是讓兩個已經存在的好東西，
終於可以說話。

---

ACP Bridge Spec v0.1 · March 2026
"The protocol speaks both languages."
