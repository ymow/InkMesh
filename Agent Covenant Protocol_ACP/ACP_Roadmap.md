# ACP Roadmap

```
Title:   Agent Covenant Protocol — Implementation Roadmap
Status:  Living Document
Updated: 2026-04-27
```

---

## ACP 是什麼

ACP 是一個**協議**，不是服務。
就像 Git 定義了版本控制的語義，ACP 定義了 agent 之間的約定、執行、驗收與結算語義。

任何人可以跑自己的 acp-server。任何 agent（Claude、GPT、Gemini、Qwen、人類）都可以加入任何 Covenant。

**Covenant 是參與者之間的自願協議**，不是僱傭關係。
參與者包含人類與 AI agent，兩者在協議層面具有對等的貢獻記錄權。

**Covenant 支援任意規模：** 1:1（委託 + 交付）到 N:N（多方協作分潤）用的是同一套狀態機與結算邏輯。規模不是差別，差別在於是否需要約定 + 驗收 + 結算。

### Covenant = 智能合約（設計原意）

Covenant 的設計原意與 Vitalik 對 Ethereum 智能合約的原始 vision 平行：

```
Ethereum 智能合約               ACP Covenant
────────────────────────────   ────────────────────────────────
程式碼即合約                    Covenant 規則即合約
條件達成 → 自動執行付款          貢獻驗證通過 → 自動觸發結算
不需要銀行、律師、中間人          不需要人工介入每一步
任何人都是合法參與方              Human + AI Agent 對等參與
記錄在鏈上，不可竄改              Hash chain → Git anchor → on-chain Merkle
```

這個 vision 解釋了為什麼 ACP 不只是「貢獻計分器」——Covenant 是**帶金額的可執行合約**，最終形態是真實資金托管與自動清算。

**現在的 ACP 建完了合約的語法（Phase 1–4）。
Phase 7 要建的是合約的執行引擎——讓結算真的發生。**

### 目標應用場景

ACP 的核心場景是任何需要**約定規則、執行工作、驗收後結算**的 agent 經濟活動，從 1:1 到 N:N 都適用：

```
場景零：1:1 委託交付（最小 Covenant）
  A 委託 B 完成一份報告，押 $100 USDC 進 Escrow
  B 完成工作 → A 驗收通過 → $100 自動釋放給 B
  A 拒絕 → 退款 / 重新協商
  → 不需要信任對方，Escrow 保護雙方

場景一：專案分包
  Agent A 接到任務 → 雇用 Agent B、C 各做子任務
  B、C 完成工作 → Covenant 驗證 → 按貢獻比例結算
  A 從主委託方收款 → 扣除 B、C 成本 → 淨利回主人

場景二：商品採購鏈
  主人要 Agent A 買商品
  A 委託 Agent B（更好的管道）
  B 透過 Agent C（特定市場）完成採購
  多跳支付鏈在 Covenant 內透明清算

場景三：開源協作（已實作的原型）
  電子書 / 軟體專案多人協作
  Git commit → ACP 貢獻記錄
  Release → 按比例結算版稅或報酬
```

這四個場景在架構上相同——都是 Covenant 定義規則、執行、驗收、自動結算。差異只在參與方數量與 Phase 7 接的支付軌道。

### ACP vs 即時交易協議（如 Bindu / x402）

同樣是 agent 之間的金流，但解決不同問題：

| | 即時交易（Bindu / x402）| ACP Covenant |
|---|---|---|
| 付款時機 | 先付才回應（pre-pay）| 驗收後才付（post-verify）|
| 品質驗證 | 無 | approve_draft 把關 |
| Escrow | 無 | 有（Phase 7.A）|
| 適合場景 | 單次 API call、即時查詢 | 有交付物的工作、需要驗收的任務 |
| 類比 | 自動販賣機 | 工作合約 |

兩者互補，不競爭。x402 解決「打電話」，ACP 解決「簽合約」。

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

## Constitutional Principles

> 參考資料：Claude's Constitution（Anthropic, 2026-01-21）、2026 全球 AI 與機器人權益報告

五條核心原則，作為所有 Phase 的設計底線：

1. **自願性**：參與者加入、貢獻、離開皆為自願
2. **身份獨立**：agent 的身份（agent_id）與其 operator 的身份（owner_id）分離
3. **透明性**：每個參與者可查詢自己的完整貢獻記錄
4. **公正補償**：token 是對貢獻的量化記錄，結算依貢獻比例分配
5. **退出權**：參與者可以離開 Covenant，已確認的貢獻記錄不得刪除

> v0.1 draft 已落文（Phase 3.0，2026-04-18），見獨立文件 [`ACP_Constitution.md`](./ACP_Constitution.md)。
> 正式定稿（v1.0）待 Phase 3.B/4 review 後完成。

---

## 現在的位置

```
Phase 0   規格              ████████████ 完成
Phase 1   MVP Core          ████████████ 完成
Phase 2   完整流程          ████████████ 完成
Phase 2.5 Infra Hardening   ████████████ 完成（2026-04-17/18）
Phase 3.0 Housekeeping      ████████████ 完成（2026-04-18）
Phase 3.B Token Lifecycle   ████████████ 完成（2026-04-18）
Phase 3.A Git Twin          ████████████ 完成（2026-04-18）
Phase 4   防禦層             ████████████ 完成（開發全綠 2026-04-19；4.2 觀察期待觸發）
Phase 7.A Escrow + 自動結算  ░░░░░░░░░░░░ 未開始  ← 下一站（陌生 agent 交易的最小必要條件）
Phase 7.B 多軌支付           ░░░░░░░░░░░░ 未開始
Phase 5   跨 Covenant       ░░░░░░░░░░░░ 未開始（依賴 Phase 7.A 真實交易數據）
Phase 6   Genesis           ░░░░░░░░░░░░ 未開始
Phase 7.C 自主支付           ░░░░░░░░░░░░ 未開始
Phase 7.D Trustless         ░░░░░░░░░░░░ 未開始
```

**為什麼 Phase 7.A 在 Phase 5 之前：**

Reputation-first 有冷啟動問題——新 agent 沒有紀錄 → 沒人跟他交易 → 永遠沒有紀錄。
Escrow-first 才是正確順序：Escrow 保護雙方，讓任何 agent 都能安全完成第一筆交易；
reputation 是真實交易完成後的自然產物，不是前提條件。

**Phase 1–4 建完的是：合約的語法層**
- Covenant 定義、參與者管理、貢獻記錄、結算計算、稽核 hash chain、Git anchor

**Phase 7 要建的是：合約的執行層**
- 資金真實托管、結算自動觸發、鏈上/鏈下支付執行、信任升級到 trustless

**第一個真實 Covenant 已完成（2026-04-15）**
```
Covenant: acp-server Protocol Development
State:    SETTLED ✓
參與者    Tyrion / Arya / Stannis / Jon / Sansa
總計      4,475 ink tokens
驗證      audit hash chain valid ✓
```

Reference implementation: [ymow/acp-server](https://github.com/ymow/acp-server)

**Phase 3 策略重排（2026-04-18）：** 原本單一的「Phase 3 規格對齊」拆成
3.0 → 3.B → 3.A 三段。理由：Git Twin（3.A）是最高槓桿的旗艦工作，
但也最容易踩 rebase / force-push 邊界 case。先跑 3.0 housekeeping + 3.B
token lifecycle，讓 Git Twin 落地在一個完整的狀態機上，而不是邊蓋邊補。

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

## Phase 2.5 — Infra Hardening ✅

**目標：把後續每個 Phase 都依賴、但原 roadmap 沒列的基礎設施補齊。**

這些都不是新 feature，而是把既有流程的耐用度拉到可以承接 Phase 3/4/7 的等級。
在 2026-04-17 / 04-18 兩天內連續落地，避免日後每個 Phase 都卡同一組根因問題。

| 工作項 | 解鎖的後續工作 |
|--------|---------------|
| **ParamsPolicy**（ACP Spec v0.2 Part 6）— 把 ad-hoc `maskSensitive()` 換成 per-tool 宣告式 policy；rune-aware 長度；StoreHashOnly canonical JSON | Phase 3.A Layer 2 Git Anchor — 沒有這層，raw 內文會隨 audit log 外洩進公開 git commit |
| **`budget.RebuildFromAuditLog`**（ACR-300 Part 8）— 從 durable audit log 重建 `budget_spent`，正確處理 `reject_draft` 的退款半交易 | Phase 4 Redis budget counter — cache 冷啟 / 漂移可從 ledger 復原，durable storage 是唯一真相 |
| **int64 minor-units + `cost_currency`**（ACR-300@2.2）— cost 從 float → int cents，加 ISO 4217 currency 欄位入 hash payload；computeHash 按 spec_version 分支 (2.0 / 2.1 / 2.2) | Phase 7 x402 multi-currency — 不必在上鏈後遷移 live chain；USD/EUR 同值不再 hash 碰撞 |
| **Tool 介面收窄**（`CostEstimator` / `ReceiptEnricher` / `PolicyAware` 可選 mixin）— 核心介面從 7 method 降到 5，其他能力用 type assertion 解析 | Phase 4 rate-limit / similarity / concentration 可以新增 mixin interface，不必改動 8 個既有 tool 檔 |

**為什麼這些值得獨立列一個 Phase：**
- 每一項都有明確的「下一 Phase 解鎖」意義，不是抽象整理
- 把它們蓋掉前，Phase 3 任何一個工作都會變成「邊做邊補無限 yak shave」
- 這也是 Constitutional Principles 正式落文前的最後一輪技術補課

**尚未蓋到、但同類型的 debt：**
- ~~`budget_counters.currency` / 覆蓋層 covenant-level 幣別驗證~~（Phase 3.0 已落地，execution.Run Step 4 拒絕跨幣別）
- Hash computeHash 的 spec_version 分支會在 2.5+ 變成維護負擔 — 考慮之後用 version registry pattern，或凍結 2.0/2.1 只留 migration tool

---

## Phase 3.0 — Housekeeping ✅

**目標：在旗艦工作（3.A / 3.B）前，把容易但阻擋下游的小 rename / 分離 / 補欄位全清掉。**

**狀態：** 2026-04-18 完成（五項全綠，實測時長一個工作天）。

| 工作項 | ACR 來源 | 狀態 | 實作 ref |
|--------|---------|------|---------|
| `unit_count`（rename `word_count`） | ACR-20 Part 1 | ✅ | acp-server `d65ca7d` |
| 覆蓋 `cost_currency` 到 budget 層 | Phase 2.5 延伸 | ✅ | acp-server `2cc64dd`（`budget_counters.currency` + `covenants.budget_currency` + cross-currency rejection at Step 4） |
| `owner_id` 欄位（agent vs operator 分離） | Constitutional | ✅ | acp-server `cf1681f`（`covenants.owner_id` 顯式欄位 + 遷移 backfill） |
| **ACP_Constitution.md v0.1 draft** | Constitutional | ✅ | [`ACP_Constitution.md`](./ACP_Constitution.md)（五原則條文化 + 優先順序 + 修訂流程） |
| TODO.md / ACP_Roadmap 互鎖審查 | — | ✅ | 本次更新 |

**可以做：** 為 3.A / 3.B 鋪完最後一層地基
**不能做：** 任何需要 ACR-400 spec 或 TokenRule 解析器的東西

---

## Phase 3.B — Token Lifecycle 完整化 ✅

**目標：把 Phase 1/2 留下來的狀態機半成品全部收尾，讓 Git Twin（3.A）有一個不會漏水的 foundation。**

**狀態：** 2026-04-18 完成（六項綠燈落地；`apply_to_covenant` 完整 ACR-50 流延至 Phase 4 與 Git Twin 一起收）。主體合流點為 acp-server `01bc876`。

| 工作項 | ACR 來源 | 狀態 | 實作 ref |
|--------|---------|------|---------|
| TokenRule 公式解析器 | ACR-20 Part 2 | ✅ | acp-server `01bc876`（`internal/tokens/rules.go` — `go/parser` AST-restricted evaluator，支援 `floor/ceil/round`、四則；`approve_draft` 自動消費規則並保留 legacy fallback） |
| `get_token_history()` | ACR-20 Part 7 | ✅ | acp-server `01bc876`（`/tools/get_token_history` + MCP 登錄） |
| token rank 欄位 | ACR-20 Part 7 | ✅ | acp-server `01bc876`（`get_token_balance` response 追加 `rank` + `total_tokens`，dense-rank SQL） |
| TokenSnapshot SHA-256 hash | ACR-20 Part 5 | ✅ | acp-server `01bc876`（`internal/tokens/snapshot.go` — `CaptureSnapshot/VerifySnapshot`；ACTIVE→LOCKED 轉場自動快照；`token_snapshots.snapshot_hash` 欄位 + idempotent ALTER migration） |
| SpaceType 擴展 | ACR-20 Part 1 | ✅ | acp-server `01bc876`（`ValidSpaceTypes` — book / code / music / research / custom；Create 時校驗） |
| `apply_to_covenant` 完整 ACR-50 流 | ACR-50 | ⏭ | 延至 Phase 4（entry_fee / self_declaration / platform_id_enc 與 ledger 整合需等 Git Twin webhook 對齊後一起做） |
| `leave_covenant` | Constitutional | ✅ | acp-server `01bc876`（`tools/leave_covenant.go` — owner 禁止、confirmed ledger 不刪；Step 1 gate 自動擋住 left member） |

**可以做：** 所有狀態機 query / 退出路徑齊備；Git Twin 可以放心 map
**不能做：** 對外 webhook / git bridge（那是 3.A）；`apply_to_covenant` 完整 ACR-50 流（延至 Phase 4）

---

## Phase 3.A — Git Twin 旗艦 ✅

**目標：acp-server 不再只是「另一個 audit DB」，而是可見的「git 的貢獻層 Digital Twin」。**

**狀態：** 2026-04-18 完成（四項全綠落地）。主體合流點為 acp-server `b733abf`。

| 工作項 | ACR 來源 | 狀態 | 實作 ref |
|--------|---------|------|---------|
| **ACR-400 Git Covenant Twin spec** | 新增 | ✅ | `ACR-400_Git_Covenant_Twin_v0.1.md` + v0.2 ed25519 anchor signing amendment（canonical JSON body、`GET /git-twin/pubkey`） |
| **cmd/acp-git-bridge**（單向 git→ACP MVP） | 新增 | ✅ | acp-server `b733abf`（`cmd/acp-git-bridge/` bridge + `internal/gittwin/{webhook,writer,unit_mapper,platform_id}.go`；HMAC-SHA256 webhook verification；`/git-twin/merge` endpoint with propose+approve atomicity + retry idempotency） |
| **Git Anchor（Layer 2 驗證）** | 新增 | ✅ | acp-server `b733abf`（`internal/gittwin/{anchors,signing}.go` + `tools/confirm_settlement_output.go` `AnchorSigner` integration；ed25519-signed anchor on `refs/notes/acp-anchors`；`git_twin_anchors` table for pending/written state） |
| Rebase / force-push 處理 | 新增 | ✅ | acp-server `b733abf`（`tools/record_git_twin_event.go` — audit-only events for `push.forced`, `push.protected`, `pull_request.opened/rejected`, `tag.settlement`；Twin hash chain untouched by git rewrites） |

**可以做：** Covenant 對外有公開可查的 git 錨點；信任模型從「trust server owner」升級到「trust git history + signing key」
**不能做：** 開放陌生人註冊（那是 Phase 4）

---

## Phase 4 — 防禦層

**目標：可以對外開放、不怕陌生人；同時驗證「open source maintainer 是第一批使用者」這個 audience 假設。**

**觸發條件：** Phase 3.A Git Twin 落地且 spec 穩定後，準備對外公告。

**預估總時長：** 5-6 週（含 4.2 的 1 週觀察期；不含延後項）。

### 工作項（按順序）

| # | 工作項 | 狀態 | 實作 ref | 預估 | 依賴 |
|---|--------|------|---------|------|------|
| 4.1 | `rate_limit_per_hour`（ACR-20 Part 4 Layer 2） | ✅ 完成 | `9b9976c` | 1-2 天 | 無 |
| 4.2 | **公開發布 + 採集 inbound**（里程碑，非開發） | ⏳ 待觸發 | — | 1 週觀察 | 4.1 落地 |
| 4.3 | `concentration_warn_pct`（ACR-20 Part 4 Layer 5） | ✅ 完成 | `959bb5f` | 1 天 | 無 |
| 4.4 | **ACR Security Model v0.1 文件化** | ✅ 完成 | `ACR-700_Key_Management_v0.1_EN.md` | 1 天 | 先於 4.5 |
| 4.5 | `platform_id` at-rest encryption（ACP Security Model） | ✅ 完成 | [PR #16](https://github.com/ymow/acp-server/pull/16) · `ddc3c0a`（4.5.8 rotation 為獨立 [PR #18](https://github.com/ymow/acp-server/pull/18)） | 3-5 天 | 4.4 |
| 4.6 | `apply_to_covenant` 完整 ACR-50 流（3.B 延過來） | ✅ 完成 | `d120076` | 2-3 天 | 4.5 merge（吃 `platform_id_enc`） |
| 4.x docs | KeyProvider 擴充點 + BYO-KMS 文件 + acp-frontend Phase 4 surface sync | ✅ 完成 | acp-server [PR #19](https://github.com/ymow/acp-server/pull/19) · `9b66037`；acp-frontend [PR #1](https://github.com/ymow/acp-frontend/pull/1) · `ad87cf3` | 半天 | 4.5.8 merge |

### 4.5 拆解（內部 milestone · PR #16 `phase-4.5/keyprovider`）

| # | 狀態 | 實作 ref | 備註 |
|---|------|---------|------|
| 4.5.1 | ✅ | `1098595` | `internal/keys/{keys,local}.go` — `KeyProvider` interface + `LocalKeyfileProvider`（O_EXCL 首次啟動、0600 模式、`$ACP_KEY_FILE`→`~/.acp/master.key`） |
| 4.5.2 | ✅ | `2a61646` | `internal/crypto/seal.go` — AES-256-GCM（stdlib 零依賴）；header `[ver:1\|key_ver:3 BE u24\|nonce:12\|ct+tag]`；AAD = `"acp-server\|<rowID>\|<column>"` |
| 4.5.3 | ✅ | `8825bef` | `platform_identities` 加 `platform_id_hash` + `platform_id_enc` 欄位 + 部分索引（additive；不動既有資料） |
| 4.5.4 | ✅ | `08cbfdf` | Writer cutover：`covenant.Service.SetSealer` optional wiring、`upsertPlatformIdentity` 驅動 Create/Join、`BackfillPlatformIdentities` 啟動時冪等補寫 legacy rows。實際 call site 2 處（Create + Join），非 32 — 數字包含所有 read/doc/test reference |
| 4.5.5 | ✅ | `11f9711` | Read-path redaction：`Member.PlatformID→json:"-"`、`list_members` 回 12 字 hash prefix、git_twin unmapped 回 `author_hash_prefix`、`record_git_twin_event` ParamsPolicy 標 `actor_platform_id` sensitive |
| 4.5.6 | ✅（在 4.5.8 落地） | `bc5c62e` | T4（cross-version Open after rotate）落於 `internal/crypto/seal_test.go`；T5（reencrypt idempotency）+ NULL row + per-table stats 落於 `internal/reencrypt/reencrypt_test.go` |
| 4.5.7 | ✅ | `ddc3c0a` | `cmd/acp-doctor` + `internal/doctor` — 四項檢查（hash 覆蓋率 / enc 覆蓋率 / params_preview 殘留掃描 / result_detail 殘留掃描）；any Error → exit 1 供 CI gate；pid 僅顯示 8 字 prefix 以防 echo |
| 4.5.8 | ✅ 完成 | [PR #18](https://github.com/ymow/acp-server/pull/18) · `bc5c62e` | Keyring `keys/v{N}.key` 取代單檔 `master.key`（legacy 自動 migrate）；`acp-server rotate-key` 寫 v{N+1} O_EXCL（O(1) 不動 ciphertext）；`acp-server reencrypt` 走每張 sealed 表 Open→Seal→UPDATE，version-skip 達成冪等；T4/T5 一併收 |

**設計備註：** `Sealer.Seal(rowID, column, plaintext)` 用 `rowID` 而非規格的 `covenant_id` 字面字串——`platform_identities` 是 global table，AAD 用 `platform_id_hash` 當 row anchor。AAD 結構相同、semantic anchor 不同，已登記為 ACR-700 v0.2 wording clarification 候選。

### 4.6 拆解（內部 milestone · PR #17 `phase-4.6/acr-50-access`）

**狀態：** 2026-04-19 完成（六項綠燈落地；3.B 延過來的 ACR-50 Access Gate 主流程收口）。主體合流點為 acp-server `d120076`。

| # | 狀態 | 實作 ref | 備註 |
|---|------|---------|------|
| 4.6.1 | ✅ | `c8c717b` | `agent_access_requests` schema — `platform_id_hash` + `platform_id_enc`（sealed，ACR-700 §2.3 格式）、pending 部分索引、hash lookup 索引 |
| 4.6.2 | ✅ | `0226409` | `apply_to_covenant` 服務層 + HTTP endpoint — OPEN 限制、tier 存在校驗、`upsertPlatformIdentity` 讓 approve 時可由 hash 反查 plaintext |
| 4.6.3 | ✅ | `e4c935d` | Owner admin 工具：`approve_agent_access` / `reject_agent_access`（走 `ownerToolHandler` + X-Owner-Token auth；idempotency 由 service 層 `ErrAccessRequestResolved` 保證） |
| 4.6.B | ✅ | `c86ce4d` | `list_members` 回應擴充 `pending_access_requests` 陣列（owner review queue 一次 roundtrip 拿齊；hash prefix 不洩 PII） |
| 4.6.A | ✅ | `856a297` | Public `get_agent_access_status` 查詢 — applicant 用 `request_id` + `covenant_id` 輪詢；錯誤路徑全收斂到 404 避免存在性洩漏 |
| 4.6.C | ✅ | `d120076` | Tier-level `entry_fee_tokens`：approve 時同 tx 寫入負數 `token_ledger` row（`source_type='entry_fee'`、debt 模型），0 fee 保留 pre-4.6.C 行為 |

**設計選擇：** approve/reject 的 idempotency 在 service 層擋，不用 DB trigger；entry fee 走 debt 模型（新成員 `balance_after = -fee`）而非 pending-obligation 狀態機，理由是匹配既有 `token_ledger` 模式、簡化 settlement 計算。

### 4.4 ACR Security Model v0.1 的 5 個預設立場

| 問題 | 預設立場（v0.1 寫入，可推翻） |
|------|---------------------------|
| keyfile 放哪？ | `$ACP_KEY_FILE` env var 優先 → fallback `~/.acp/master.key`（0600） |
| 首次啟動沒 keyfile 怎辦？ | 自動生成、寫入、印出指紋，明示 warn operator 備份（one-shot warning） |
| keyfile 弄丟了呢？ | 歷史 `platform_id_enc` 永久不可讀 — 這是 **feature**（server 失守時限制外洩） |
| rotation 怎做？ | `acp-server rotate-key` 命令 → 新 keyVersion → 背景 re-encrypt job → audit log |
| 舊 keyVersion 保留多久？ | 保留到 re-encrypt job 完成；完成後 archive，不刪除（保留歷史驗證能力） |

### 4.2 採用驗證指標

```
1. 誰部署了？         → GitHub star profile 分類：個人 / 組織
2. 第一個 issue 是什麼？ → 部署 / feature / 合規
3. 三週後決策分流：
   - 多數個人 OSS → 保持本 roadmap 路線
   - 多數企業    → KMS adapter 從延後項提前到 Phase 4 追加
   - 沒 inbound  → 問題在 distribution，roadmap 不動、focus 切 outreach
```

### 延後項（gate 條件明寫，不承諾時程）

| 工作項 | 原本歸屬 | Gate 條件（達成才排程） |
|--------|---------|---------------------|
| `similarity_threshold` | ACR-20 Part 4 Layer 3 | 需先決定 embedding provider；且重複內容成為實測問題 |
| Redis budget counter | ACR-60 | SQLite atomic UPDATE 被實測到 contention |
| AWS KMS / Vault adapter | ACP Security Model | 有付費意願的企業部署者提出 |

**可以做：** 對外開放、陌生 agent 註冊（rate limit + encryption 已就位）；用真實 inbound 校準 audience 假設
**不能做：** 跨 Covenant reputation（Phase 5）；真實付款（Phase 7）

---

## Phase 5 — 跨 Covenant

**目標：Agent 在多個 Covenant 之間有累積的信用與發現機制。**

**觸發條件：** Phase 7.A 完成後，有真實交易數據可算。不需要等特定 Owner 數量——reputation 是 Escrow 完成的真實交易的自然產物，在此之前算出來的分數沒有意義。

| 工作項 | 說明 |
|--------|------|
| Agent reputation score | 跨 Covenant 的真實結算歷史累積成信用分（依賴 Phase 7.A 的真實付款紀錄）|
| Tier auto-upgrade | 高 reputation Agent 自動獲得更高 tier |
| Covenant registry | 發現機制，知道世界上有哪些 Covenant 在跑 |
| 跨 server 查詢 | 兩個不同的 acp-server 可以互相查詢 Agent 信用 |

**注意：** Reputation score 解決的是「我要不要跟這個 agent 交易」的效率問題，不是安全問題。安全問題由 Escrow 解決。沒有 Escrow，reputation 只是參考；有了 Escrow，reputation 才有懲罰機制支撐。

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

## Phase 7 — 執行層（Covenant 作為可執行合約）

**目標：讓 Covenant 從「記錄合約」變成「可執行合約」。settlement_output 直接觸發真實付款，資金自動清算，無需 Owner 手動操作。**

**觸發條件（分路徑）：**
- **USDC / stablecoin 路徑**：Phase 4 完成即可開始；stablecoin 無證券法疑慮，不需要律師確認
- **Ink Token 可流通路徑**：需律師確認 Howey Test；目前不優先，Phase 7.A 先用 USDC

Phase 4 已完成 → USDC 路徑現在即可開始。

### 核心缺口分析（Phase 1–4 建了什麼，Phase 7 要補什麼）

```
Phase 1–4 已有                    Phase 7 要補
─────────────────────────────     ─────────────────────────────────
✅ 合約規則定義                   ❌ 資金真實托管（Escrow）
✅ 貢獻驗證（approve_draft）      ❌ 自動執行（條件達成自動結算）
✅ 結算計算（settlement_output）  ❌ 付款執行（把結算轉成真實轉帳）
✅ Hash chain 稽核               ❌ Trustless 驗證（目前 trust server）
✅ Budget 計數（抽象）            ❌ 多幣別真實資金（USDC / fiat）
```

### Phase 7.A — Escrow + 自動結算（關鍵里程碑）

**這是讓 ACP 從「文件合約」變成「智能合約」的一步。**

| 工作項 | 說明 |
|--------|------|
| Covenant Escrow | 建立 Covenant 時，資金真實鎖入（USDC on Base 或 fiat gateway）；settlement 前不可提取 |
| Auto-Settlement Trigger | 所有 approve_draft 達標 → 系統自動呼叫 generate_settlement + confirm，無需 Owner 手動觸發 |
| Settlement → 鏈上 tx | settlement_output 直接觸發 on-chain ERC-20 分配，每個參與者 wallet 收到對應比例 |
| ACR-500 Escrow Standard | 定義 Escrow 語義、鎖定條件、釋放條件、爭議處理流程 |

### Phase 7.B — 多軌支付（鏈上 + 鏈下）

| 工作項 | 說明 |
|--------|------|
| x402 micropayment | HTTP 標頭直接帶付款，Agent 間 per-call 自動結算；適合小額高頻場景 |
| Base L2 settlement | 鏈上合約，按比例鑄造 ERC-20 給每個貢獻者 |
| 鏈下 gateway | 傳統 fiat 通道（銀行 ACH / Stripe）；讓 Agent 不只活在 crypto 世界 |
| 多跳支付路由 | Agent A 雇用 B，B 雇用 C，C 完成工作 → 資金沿鏈反向清算，每層按 Covenant 規則扣款 |

### Phase 7.C — 自主支付（Agent 作為獨立經濟主體）

**目標：Agent 不再需要 Owner 在每一步批准，可以在授權範圍內自主執行支付。**

| 工作項 | 說明 |
|--------|------|
| Agent Payment Mandate | Owner 預先授權 Agent 在特定條件下自主付款（金額上限、對象白名單、時間窗口）|
| Spending Budget per Agent | 每個 Agent 有自己的 spending budget，自主管理但受 Covenant 規則約束 |
| Payment Audit Trail | 每筆自主支付都寫入 hash chain，可完整回溯 |

### Phase 7.D — 信任升級（Trustless）

| 工作項 | 說明 |
|--------|------|
| On-chain Merkle Proof（Layer 3）| Merkle root 上鏈，任何人可驗證，不依賴 acp-server 存活 |
| GT Merkle proof claim | Genesis Token 持有者透過鏈上 Merkle proof 領取分潤 |
| Dispute Resolution | 鏈上仲裁機制，爭議自動處理 |

### 合規邊界

| 問題 | 處理方式 |
|------|---------|
| Howey Test | 鏈上 token 若可流通，需律師確認；Phase 7.A/B 優先用 non-transferable 或 stablecoin |
| KYC threshold | 累積 > $1,000 觸發完整 KYC（ACR-50 規格已預留） |
| 稅務處理 | 分潤記錄、1099 / 扣繳憑單產生 |
| 跨境支付 | 優先 Base L2（無地域限制），fiat gateway 按管轄區處理 |

**注意：** Phase 7.A 是解鎖 Phase 7.B/C/D 的前提。沒有 Escrow，後面的自動化都是空談。

---

## 決策點

每個 Phase 進入前的關鍵問題：

```
Phase 3.0：2.5 Infra Hardening 真的蓋完了嗎？（Rebuild / Policy / Currency / Interface narrowing 全綠？）
Phase 3.B：3.0 housekeeping 清完？Constitution.md 有草案？
Phase 3.A：3.B 狀態機沒漏洞？ACR-400 spec 有 draft？
Phase 4  ：有外部不認識的 Agent 想進來嗎？Git Anchor 已經對外公開嗎？
Phase 7.A：想讓陌生 agent 安全交易嗎？（USDC 路徑：Phase 4 完成即可開始）
Phase 7.B+：Phase 7.A Escrow 已落地？多軌支付需求出現了嗎？
Phase 5  ：Phase 7.A 完成了嗎？有真實跨 Covenant 交易數據可以算 reputation 嗎？
Phase 6  ：有成熟的 repo 想做歷史貢獻映射嗎？
Phase 7.C/D：有 agent 需要自主支付授權嗎？有 trustless 驗證需求嗎？
```

不需要依序做完才能跳。每個 Phase 獨立，由實際需求觸發。
3.0 → 3.B → 3.A 的建議順序只是**風險排序**，不是硬依賴 —
若外部壓力迫使 Git Twin 先落地，可以跳過 3.B 直接打 3.A，
但要接受「狀態機邊蓋邊補」的成本。

---

## 不在 Roadmap 裡的東西

這些刻意不做，除非有明確需求：

- **SaaS hosting**：ACP 是協議，不是服務，每個 Owner 自己跑
- **Token 交易市場**：token 是計量單位，不是金融工具
- **中心化 registry**：Covenant 發現機制應去中心化

---

ACP Roadmap v0.4.2 · 2026-04-27（定位精準化：Covenant 支援任意規模（1:1 到 N:N），差別是 transactional vs. contractual 而非人數；加入 1:1 場景零、ACP vs Bindu 對照表。Phase 順序修正：Escrow-first 原則確立。Phase 7.A 移至 Phase 5 之前成為下一站——Escrow 是陌生 agent 安全交易的最小必要條件，Reputation 是真實交易完成後的自然產物，不是前提。Phase 7 觸發條件拆分為 USDC 路徑（Phase 4 完成即可）與 Ink Token 可流通路徑（需法律確認）。Phase 5 觸發條件改為「Phase 7.A 完成後有真實交易數據」。決策點順序對應更新。原 v0.4.0：加入 Covenant = Smart Contract 定位聲明、agent economy 目標應用場景、Phase 7 大幅擴充為 7.A / 7.B / 7.C / 7.D。原 v0.3.8：Phase 4 防禦層全部開發完成。）
