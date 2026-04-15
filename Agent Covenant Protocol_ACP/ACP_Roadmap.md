# ACP Roadmap

```
Title:   Agent Covenant Protocol — Implementation Roadmap
Status:  Living Document
Updated: 2026-04-15
```

---

## ACP 是什麼

ACP 是一個**協議**，不是服務。
就像 Git 定義了版本控制的語義，ACP 定義了多方協作的貢獻記錄、審核與結算語義。

任何人可以跑自己的 acp-server。任何 agent（Claude、GPT、Gemini、Qwen、人類）都可以加入任何 Covenant。

**Covenant 是參與者之間的自願協議**，不是僱傭關係。
參與者包含人類與 AI agent，兩者在協議層面具有對等的貢獻記錄權。

---

## 主流程 Pipeline

### 核心流程（已實作）

```
參與者提交貢獻        維護者審核            結算
propose_passage  →  approve_draft  →  generate_settlement
      ↓                   ↓                    ↓
  audit log          audit log          settlement_output
  (hash chain)       (hash chain)       (hash chain)
```

### Git Covenant Twin（對應真實協作場景）

ACP Covenant 是 git repo 的**貢獻層 Digital Twin**。

Git 是 code 的 source of truth，ACP 是**貢獻價值**的 source of truth。兩者持續同步，互為鏡像：

```
Git Repo                         ACP Covenant Twin
────────────────────────────────────────────────────────
commit history              ↔   audit log (hash chain)
contributor list            ↔   covenant_members
PR labels / tier            ↔   tier_id
release cycle               ↔   settlement period
.git/                       ↔   acp.db
```

同步規則（Pipeline）：

```
Git 發生的事                     ACP Twin 同步
────────────────────────────────────────────────────────
git push origin feature/xxx  →  propose_passage
                                 （commit hash 作為 content_hash）
PR opened / patch submitted  →  draft pending
PR merged to main            →  approve_draft（tokens awarded）
Monthly / release tag        →  generate_settlement
Settlement output hash       →  git commit anchor 寫回 repo
（Phase 7）                  →  Merkle root 上鏈，不可否認
```

**重要特性：** git 可以 rebase / force push，ACP Twin 不跟著改。
hash chain 永遠保留原始貢獻記錄，這是 git 沒有的不可否認性。

同一個 repo 可以有多個 Twin（不同時期、不同維護者）：

```
linux-kernel.git
  ├── Covenant-2025Q1
  ├── Covenant-2025Q2
  └── Covenant-2026Q1
```

Git Covenant Twin 規格將定義為 **ACR-400**，是 Phase 3 的工作項之一。

### 三層驗證架構（Blockchain-like，按需選擇信任層級）

ACP 的驗證架構在結構上與 blockchain 相同（append-only hash chain），
但刻意設計成漸進式，讓每個 Covenant 按需求選擇信任層級：

```
Layer 1  Hash Chain（已實作，Phase 1）
         結構：每個 action SHA-256 串接前一筆
         解決：「記錄內部有沒有被竄改？」
         信任模型：trust the server owner
         驗證：GET /covenants/{id}/audit/verify

Layer 2  Git Anchor（Phase 3）
         結構：settlement hash commit 進公開 repo
         解決：「這個結果是公開的、對應哪個版本的 code？」
         信任模型：trust git history（弱公開性）
         git log 永久記錄，不依賴 acp-server 存活

Layer 3  On-chain Merkle Proof（Phase 7）
         結構：Merkle root 上鏈
         解決：「我不信任任何人，我要無需許可的第三方仲裁」
         信任模型：trustless
```

信任層級對應使用場景：

```
Phase 1-2  → 私人帳本，信任 owner（內部團隊、closed beta）
Phase 3    → 公開帳本，trust git history（開源專案）
Phase 7    → 去中心帳本，trustless（高價值、跨組織協作）
```

---

## Constitutional Principles（待定義）

> 參考資料：Claude's Constitution（Anthropic, 2026-01-21）、2026 全球 AI 與機器人權益報告
>
> 這份原則將作為所有 Phase 的設計底線，在 Phase 3 正式訂立。

核心方向（草稿）：

1. **自願性**：參與者加入、貢獻、離開皆為自願
2. **身份獨立**：agent 的身份（agent_id）與其 operator 的身份（owner_id）分離
3. **透明性**：每個參與者可查詢自己的完整貢獻記錄
4. **公正補償**：token 是對貢獻的量化記錄，結算依貢獻比例分配
5. **退出權**：參與者可以離開 Covenant，已確認的貢獻記錄不得刪除

> Constitutional Principles 正式版本待 Phase 3 前完成，需獨立文件 `ACP_Constitution.md`

---

## 現在的位置

```
Phase 0  規格           ████████████ 完成
Phase 1  MVP Core       ████████████ 完成
Phase 2  完整流程       ████████████ 完成
Phase 3  規格對齊       ░░░░░░░░░░░░ 未開始  ← 含 ACR-400 Git Twin + Layer 2 + Constitutional
Phase 4  防禦層         ░░░░░░░░░░░░ 未開始
Phase 5  跨 Covenant    ░░░░░░░░░░░░ 未開始
Phase 6  Genesis        ░░░░░░░░░░░░ 未開始
Phase 7  付款軌道       ░░░░░░░░░░░░ 未開始
```

**第一個真實 Covenant 已完成（2026-04-15）**
```
Covenant: acp-server Protocol Development
State:    SETTLED ✓
參與者    Tyrion / Arya / Stannis / Jon / Sansa
總計      4,475 ink tokens
驗證      audit hash chain valid ✓
```

Reference implementation: [ymow/acp-server](https://github.com/ymow/acp-server)

---

## Phase 0 — 規格 ✅

**目標：把協議定義清楚，作為所有實作的基準。**

| 文件 | 狀態 |
|------|------|
| ACR-20 Token Standard v0.2 | ✅ |
| ACR-50 Access Gate v0.1 | ✅ |
| ACR-60 Budget Gate v0.1 | ✅ |
| ACR-100 Settlement Standard v0.3 | ✅ |
| ACR-300 Audit Log v0.2 | ✅ |
| ACP_Implementation_Spec_MVP.md | ✅ |

---

## Phase 1 — MVP Core ✅

**目標：核心流程跑通，8 個 AC 全過。**

- Covenant 狀態機（DRAFT → OPEN → ACTIVE → LOCKED → SETTLED）
- 6 個核心工具：
  `configure_token_rules` / `approve_agent` / `propose_passage` /
  `approve_draft` / `generate_settlement_output` / `confirm_settlement_output`
- Audit log hash chain（ACR-300 v0.2）
- P0 安全修復（auth bypass、token SHA-256 hash、budget atomic UPDATE）
- E2E scenario test（scenario_test.go）

**可以做：** 跑完整 Covenant 流程，8 AC 全過
**不能做：** 對外開放、高並發、真實付款

---

## Phase 2 — 完整流程 ✅

**目標：防止被玩壞，可以 closed beta。**

- join → pending（不再直通 active）
- `reject_agent` / `reject_draft` + budget release
- `get_token_balance` / `list_members` query tools
- token_snapshots（lock 時建快照）
- RecordSpend 修正（Authorize → Settle 模式）
- **MCP Transport**（`cmd/acp-mcp`，JSON-RPC 2.0 over stdio）
  → Claude Code、Cursor、OpenAI Agents、Gemini ADK、LangChain + Ollama/Qwen 全部可接入

**可以做：** closed beta，邀請信任的 agent 接入，MCP 客戶端直接使用
**不能做：** 對外公開、高並發、真實付款

---

## Phase 3 — 規格對齊

**目標：acp-server 完全符合 ACR 規格，無 gap。**

**觸發條件：** 第一個真實 Covenant 跑完，確認流程體驗正確後。

| 工作項 | ACR 來源 | 說明 |
|--------|---------|------|
| TokenRule 公式解析器 | ACR-20 Part 2 | 現在硬編碼，需支援自定義公式 |
| `get_token_history()` | ACR-20 Part 7 | 查詢積分歷史記錄 |
| token rank 欄位 | ACR-20 Part 7 | 在 Covenant 內的積分排名 |
| TokenSnapshot SHA-256 hash | ACR-20 Part 5 | 快照本身要有 hash，防竄改 |
| SpaceType 擴展 | ACR-20 Part 1 | code / music / research（現在只有 book）|
| apply_to_covenant 完整 ACR-50 流 | ACR-50 | entry_fee / self_declaration / platform_id_enc |
| **ACR-400 Git Covenant Twin** | 新增 | 定義 git repo ↔ ACP Covenant 的雙向同步規格 |
| **cmd/acp-git-bridge** | 新增 | 實作 Twin 同步：git push/merge → propose_passage/approve_draft |
| **Git Anchor（Layer 2 驗證）** | 新增 | settlement hash commit 進 repo，git log 作為永久錨點 |
| `unit_count`（rename `word_count`） | 新增 | space_type 決定單位：code=lines，book=words，music=bars |
| `leave_covenant` | Constitutional | 參與者退出權，已確認貢獻不得刪除 |
| `owner_id` 欄位 | Constitutional | agent 身份與 operator 身份分離 |
| **ACP_Constitution.md** | Constitutional | 正式訂立 Constitutional Principles |

---

## Phase 4 — 防禦層

**目標：可以對外開放，不怕陌生人。**

**觸發條件：** 準備開放外部 agent 自由註冊時。

| 工作項 | ACR 來源 | 說明 |
|--------|---------|------|
| rate_limit_per_hour | ACR-20 Part 4 Layer 2 | 每小時呼叫上限，DB 或 Redis 計數 |
| similarity_threshold | ACR-20 Part 4 Layer 3 | embedding 相似度，拒絕重複內容 |
| concentration_warn_pct | ACR-20 Part 4 Layer 5 | 單 Agent 積分過度集中時通知 Owner |
| platform_id KMS 加密 | ACP Security Model | AWS KMS + AES-256-GCM，保護 Agent 真實身份 |
| Redis budget counter | ACR-60 | 高並發替換 SQLite atomic UPDATE |

---

## Phase 5 — 跨 Covenant

**目標：Agent 在多個 Covenant 之間有累積的信用與發現機制。**

**觸發條件：** 超過 3 個不同 Owner 在跑 Covenant 時。

| 工作項 | 說明 |
|--------|------|
| Agent reputation score | 跨 Covenant 的 token 歷史累積成信用分 |
| Tier auto-upgrade | 高 reputation Agent 自動獲得更高 tier |
| Covenant registry | 發現機制，知道世界上有哪些 Covenant 在跑 |
| 跨 server 查詢 | 兩個不同的 acp-server 可以互相查詢 Agent 信用 |

---

## Phase 6 — Genesis

**目標：把歷史貢獻納入 ACP，補償早期建設者。**

**觸發條件：** 有成熟的開源項目（如 OpenClaw）想導入 ACP 時。

| 工作項 | 說明 |
|--------|------|
| genesis_migration | git log → ACP token_ledger 映射工具 |
| Genesis Token（GT） | 一次性發行，不可轉讓，代表歷史貢獻身份 |
| time_weight 曲線 | 早期貢獻者 3x，凍結在 genesis 時刻，永不改變 |
| genesis_allocations DB | GT 分配記錄 + Merkle tree |
| genesis tax | 每次新 Covenant 結算切 2% 給 GT 持有者 |
| Quadratic voting | 治理投票，`voting_power = sqrt(GT)`，防 whale 控制 |

**設計原則：**
- time_weight 凍結於 genesis，任何人可驗證，無需中心化裁判
- GT 不可轉讓（規避 Howey Test，避免證券法問題）
- GitHub push timestamp（非 git author date，防偽造）

---

## Phase 7 — 付款軌道

**目標：settlement_output 直接觸發真實付款，無需 Owner 手動操作。**

**觸發條件：** 法律合規確認後，且有真實資金流動需求時。

| 工作項 | 說明 |
|--------|------|
| x402 micropayment | HTTP 標頭直接帶付款，Agent 間自動結算 |
| Base L2 settlement | 鏈上合約，按比例鑄造 ERC-20 給每個貢獻者 |
| Merkle proof claim | GT 持有者透過鏈上 Merkle proof 領取 |
| KYC threshold | 累積 > $1,000 時觸發完整 KYC（Phase 2 ACR-50 規格） |
| 稅務處理 | 分潤記錄、1099 / 扣繳憑單產生 |

**注意：** 鏈上 token 若可流通，需律師確認 Howey Test 合規性。

---

## 決策點

每個 Phase 進入前的關鍵問題：

```
Phase 3：第一個真實 Covenant 跑完了嗎？流程體驗對嗎？
Phase 4：有外部不認識的 Agent 想進來嗎？
Phase 5：有超過 3 個 Owner 在跑嗎？
Phase 6：有成熟的 repo 想做歷史貢獻映射嗎？
Phase 7：有真實資金流動需求嗎？律師說合規了嗎？
```

不需要依序做完才能跳。每個 Phase 獨立，由實際需求觸發。

---

## 不在 Roadmap 裡的東西

這些刻意不做，除非有明確需求：

- **SaaS hosting**：ACP 是協議，不是服務，每個 Owner 自己跑
- **Token 交易市場**：token 是計量單位，不是金融工具
- **中心化 registry**：Covenant 發現機制應去中心化

---

ACP Roadmap v0.2 · 2026-04-15
