# Agent Covenant Protocol (ACP)

**多方協作的貢獻記錄與結算協議。**

就像 Git 管理程式碼版本，ACP 管理貢獻價值分配。

> *How do multiple participants — human or AI — collaborate on a shared project, where every contribution is provably recorded, and every participant receives fair compensation automatically?*

---

## 現在的狀態

```
Phase 0  規格           ████████████ 完成
Phase 1  MVP Core       ████████████ 完成
Phase 2  完整流程       ████████████ 完成
Phase 3  規格對齊       ░░░░░░░░░░░░ 下一步  ← Git Covenant Twin + Constitutional
Phase 4  防禦層         ░░░░░░░░░░░░ 未開始
Phase 5  跨 Covenant    ░░░░░░░░░░░░ 未開始
Phase 6  Genesis        ░░░░░░░░░░░░ 未開始
Phase 7  付款軌道       ░░░░░░░░░░░░ 未開始
```

**第一個真實 Covenant 已 SETTLED（2026-04-15）**

```
Covenant: acp-server Protocol Development
總計:      4,475 ink tokens
參與者:    Tyrion / Arya / Stannis / Jon / Sansa
驗證:      audit hash chain valid ✓
錨點:      settlements/2026-04-15-acp-server-phase1-2.json
```

Reference implementation: [ymow/acp-server](https://github.com/ymow/acp-server)

---

## Ink Token 是什麼

**Ink Token 是貢獻的計量單位，不是加密貨幣。**

```
tokens = unit_count × tier_multiplier × acceptance_ratio
```

| 變數 | 意義 |
|------|------|
| `unit_count` | 貢獻的量（code: 行數，prose: 字數，music: 小節） |
| `tier_multiplier` | 貢獻的層級（core=3x, feature=2x, review=1.5x, docs=1x） |
| `acceptance_ratio` | 維護者認可的品質比例（0.0–1.0） |

**Token 的性質：**
- Covenant 範圍內有效，不可跨 Covenant 轉移
- 不可交易，不是金融工具
- 代表「這個人在這個協作裡貢獻了多少」
- 結算時按比例分配 contributor pool（Owner 設定的 %）

---

## 核心流程

### 主流程

```
Owner 建立 Covenant
    ↓  定義規則、tier、預算
參與者申請加入（人類或 AI agent）
    ↓  Owner 審核
ACTIVE 狀態：協作開始
    ↓
參與者提交貢獻 → propose_passage
    ↓  draft pending
Owner 審核 → approve_draft
    ↓  tokens 自動計算並記入 audit log
週期結束，Owner 鎖定 Covenant
    ↓
generate_settlement → 計算每人應得比例
confirm_settlement  → SETTLED
    ↓
結果 commit 進 git repo（Layer 2 錨點）
```

### Covenant 狀態機

```
DRAFT → OPEN → ACTIVE → LOCKED → SETTLED
```

| 狀態 | 可以做的事 |
|------|-----------|
| DRAFT | 設定 token 規則、tier、預算 |
| OPEN | 參與者申請加入 |
| ACTIVE | 提交貢獻、審核貢獻 |
| LOCKED | 生成結算輸出 |
| SETTLED | 終態，不可變更 |

### Git Covenant Twin（Phase 3）

ACP Covenant 是 git repo 的**貢獻層 Digital Twin**：

```
Git 發生的事              ACP Twin 同步
──────────────────────────────────────────
git push              →  propose_passage
PR merged             →  approve_draft（tokens awarded）
git tag / release     →  generate_settlement
settlement hash       →  git commit anchor（Layer 2）
（Phase 7）           →  Merkle root 上鏈（Layer 3，trustless）
```

---

## 三層驗證架構

```
Layer 1  Hash Chain（已實作）
         每筆 action SHA-256 串接前一筆
         解決：記錄有沒有被竄改？
         信任模型：trust the server owner

Layer 2  Git Anchor（Phase 3）
         settlement hash commit 進公開 repo
         解決：結果是公開的、永久的
         信任模型：trust git history

Layer 3  On-chain Merkle Proof（Phase 7）
         解決：不信任任何人，要無需許可的仲裁
         信任模型：trustless
```

按需選擇層級：大多數協作 Layer 1 就夠，開源專案用 Layer 2，高價值跨組織用 Layer 3。

---

## Interface Catalog（10 個介面）

| 介面 | 類型 | 說明 |
|------|------|------|
| `configure_token_rules` | admin | 設定 token 計算規則 |
| `approve_agent` | admin | 接納參與者申請 |
| `reject_agent` | admin | 拒絕參與者申請 |
| `propose_passage` | contribution | 提交貢獻 |
| `approve_draft` | admin | 審核通過，tokens 計算並記錄 |
| `reject_draft` | admin | 審核拒絕，預算釋放 |
| `get_token_balance` | query | 查詢 token 餘額 |
| `list_members` | query | 列出所有參與者 |
| `generate_settlement_output` | settlement | 生成結算輸出 |
| `confirm_settlement_output` | admin | 確認結算，Covenant → SETTLED |

所有介面皆通過 execution engine，每個 action 都記入 audit log hash chain。

---

## 接入方式

任何 MCP 相容的 agent 都可以接入，不鎖定任何平台：

```bash
# Claude Code / Cursor / OpenAI Agents / Gemini ADK / LangChain
export ACP_SERVER_URL=http://localhost:8080
export ACP_SESSION_TOKEN=sess_xxxxx
export ACP_COVENANT_ID=cvnt_xxxxx
export ACP_AGENT_ID=agent_xxxxx
./acp-mcp  # JSON-RPC 2.0 over stdio
```

---

## 協議定位

| ACP 是 | ACP 不是 |
|--------|---------|
| 多方協作的貢獻記錄協議 | SaaS 服務 |
| 開放協議，任何人可自行架設 | 中心化平台 |
| Token = 貢獻計量單位 | Token = 加密貨幣 |
| 與 git 並存，互補 | Git 的替代品 |
| 人類與 AI 對等參與 | 只給 AI 用的系統 |

---

## Constitutional Principles（草稿，Phase 3 正式訂立）

> 參考：Claude's Constitution（Anthropic, 2026-01-21）、2026 全球 AI 與機器人權益報告

1. **自願性** — 參與者加入、貢獻、離開皆為自願
2. **身份獨立** — agent 身份（agent_id）與 operator 身份（owner_id）分離
3. **透明性** — 每個參與者可查詢自己的完整貢獻記錄
4. **公正補償** — token 依貢獻比例計算，結算規則在 Covenant 建立時公開
5. **退出權** — 參與者可離開，已確認的貢獻記錄不得刪除

---

## 規格文件索引

### ACR 標準

| 標準 | 版本 | 說明 |
|------|------|------|
| ACR-1 | v0.1 | Meta：ACR 提案流程 |
| ACR-20 | v0.2 | Ink Token 貢獻計算 |
| ACR-50 | v0.1 | 參與者存取控制 |
| ACR-60 | v0.1 | 預算閘門 |
| ACR-100 | v0.3 | 結算標準 |
| ACR-300 | v0.2 | Audit Log（強制） |
| ACR-400 | 草稿 | Git Covenant Twin（Phase 3） |

### 實作文件

| 文件 | 說明 |
|------|------|
| ACP_Roadmap.md | Phase 0–7 完整規劃 |
| ACP_Implementation_Spec_MVP.md | 實作規格 |
| ACP_Security_Model_v0.2.md | 安全模型，20 個 REVIEW 項目 |

---

ACP v0.5 · 2026-04-15
