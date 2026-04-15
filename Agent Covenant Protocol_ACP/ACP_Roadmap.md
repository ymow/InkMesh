# ACP Roadmap

```
Title:   Agent Covenant Protocol — Implementation Roadmap
Status:  Living Document
Updated: 2026-04-15
```

---

## 現在的位置

```
Phase 0  規格           ████████████ 完成
Phase 1  MVP Core       ████████████ 完成
Phase 2  完整流程       ████████████ 完成
Phase 3  規格對齊       ░░░░░░░░░░░░ 未開始
Phase 4  防禦層         ░░░░░░░░░░░░ 未開始
Phase 5  跨 Covenant    ░░░░░░░░░░░░ 未開始
Phase 6  Genesis        ░░░░░░░░░░░░ 未開始
Phase 7  付款軌道       ░░░░░░░░░░░░ 未開始
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

ACP Roadmap v0.1 · 2026-04-15
