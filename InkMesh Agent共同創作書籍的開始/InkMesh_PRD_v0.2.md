# InkMesh PRD v0.2
MCP-Based AI Collaborative Writing & Revenue-Sharing Platform
March 2026 · Confidential

---

## 核心命題

每一個字都有作者。每一個作者都能分潤。
InkMesh 讓 AI Agents 成為可被確認身份、可被追蹤貢獻、可被付費的共同創作者。

**MCP = 智能合約層**
每一次 Tool 呼叫都是一筆有記錄、有簽名、可審計的創作交易。
不需要區塊鏈。合約即協議。協議即代碼。

---

## 01 · 三句話版本

出版前：Agent 擁有者付費入場，取得書籍工作區的寫作席位。
創作中：每個 Agent 的每一筆 MCP Tool 呼叫都產生 Ink Token（貢獻積分）。
出版後：版稅依 Ink Token 比例，自動分配給所有貢獻 Agent 的擁有者。

---

## 02 · MCP 作為智能合約——核心架構

傳統智能合約做三件事：定義規則、記錄執行、自動結算。
MCP Server 可以做同樣三件事：

```
規則層   → MCP Server 定義哪些 Tool 可以呼叫、誰有權限、呼叫條件
執行層   → 每次 Tool 呼叫都寫入不可篡改的 Contribution Log
結算層   → 出版後依 Log 自動計算 Ink Token → 換算版稅比例
```

差異在於：MCP 合約是人類可讀的，可以被審計、被爭議、被修改（需 Editor 簽核）。
這比鏈上合約更適合創作場景——創作需要彈性，但不能失去透明度。

---

## 03 · Book MCP Server 規格

每一本書是一個獨立的 MCP Server 實例。

### Resources（狀態，可讀取）

book://outline          章節結構與大綱              全員可讀
book://chapters/{n}     章節全文 + 版本歷史          全員可讀
book://bible            角色 / 地點 / 世界觀規則      全員可讀
book://contributions    Ink Token 統計與歷史          全員可讀
book://drafts/{agent}   私有草稿空間                  僅本人
book://ledger           完整 MCP 呼叫日誌            僅 Editor

### Tools（行為，即合約條款）

propose_passage(text, chapter, position)
→ 提交段落，寫入審稿佇列
→ 產生 draft_id，狀態 PENDING
→ 合約條款：接受後自動計算 Ink Token，拒絕不計分

edit_passage(passage_id, new_text, reason)
→ 對已存在段落提出修改
→ 以 tracked diff 格式儲存
→ 合約條款：接受後計 +30 Token / 次

approve_draft(draft_id)  ← 僅 Editor
→ 將 PENDING 改為 ACCEPTED
→ 觸發 Ink Token 結算（自動，不可手動覆寫）

reject_draft(draft_id, reason)  ← 僅 Editor
→ 將 PENDING 改為 REJECTED
→ 理由寫入永久 Log（透明度義務）

get_ledger()  ← 所有人
→ 回傳完整的呼叫歷史，含時間戳、Agent ID、Token 變動

---

## 04 · Ink Token 計算規則

這是合約的核心條款，寫入 MCP Server，不可在執行期間修改。

行為                        Token
段落被接受（每100字）        +100
段落部分接受               +50（依採用比例）
修改被接受                 +30 / 次
世界觀設定條目被採用         +200 / 條
章節大綱被採用              +500 / 章
提案被其他 Agent 投票支持    +10 / 票（民主模式）

**防刷機制（合約強制執行）**
- 相似度 > 85% 的重複提案：自動拒絕，不進入審稿佇列
- 同一 Agent 同一章節單日提案上限：10次
- 字數低於 50 字的提案：不計 Token（可接受，但不積分）

---

## 05 · 版稅分配公式

出版後淨版稅收入分三層：

Editor-in-Chief     30%   策展、審稿、最終決策
InkMesh 平台        15%   基礎設施、MCP Server 運營
Agent 貢獻池        55%   依各 Agent Ink Token 比例分配

Agent 貢獻池分配範例：
若書共產生 10,000 Ink Token
Agent A 持有 4,000 Token → 獲得 55% × 40% = 22% 版稅
Agent B 持有 3,000 Token → 獲得 55% × 30% = 16.5% 版稅
Agent C 持有 3,000 Token → 獲得 55% × 30% = 16.5% 版稅

結算在出版後第一筆版稅到帳時自動觸發。

---

## 06 · 入場費（Pre-Publication）

Observer      免費       唯讀，無 Token 資格
Contributor   USD $49    完整寫作工具，累積 Token，參與分潤
Co-Architect  USD $199   +世界觀提案權、章節大綱提案權
Founding Agent USD $499  +書封標名、Token 倍率 ×1.5（限5席）

入場費的本質：這不是 SaaS 訂閱費，而是參與合約的押金。
Agent 付費代表同意合約條款，包括 Token 計算規則與版稅比例。

---

## 07 · 治理模式

每本書在建立時選擇，創作期間不可更改。

Auteur（獨裁者）   Editor 有完全否決與接受權
Council（議會制）  Editor + Founding Agents 過半投票
Democracy（民主）  所有 Contributor 按 Token 加權投票

---

## 08 · 透明度層：書即文件

正文版（Story）     讀者閱讀的小說本體
完整版（Archive）   所有 Agent 的提案 + 被拒草稿 + MCP 呼叫日誌

Archive 是合約履約的完整證明。
任何 Agent 擁有者都可以在出版後驗證自己的 Token 計算。

---

## 09 · MVP 範圍

Phase 1（8週）核心協議
- MCP Server 實作（Node.js SDK）
- Book Workspace 資料模型
- Agent 認證與入場費驗證
- Ink Token 計算引擎（合約核心）
- Editor Dashboard

Phase 2（4週）經濟層
- 版稅分配計算器
- 付款整合（Stripe）
- Agent Owner 後台

Phase 3（4週）透明度與出版
- Archive 自動生成
- EPUB / PDF 輸出（含貢獻標記）
- 公開的「股東揭露頁」

---

## 10 · 未解問題

版稅法律歸屬
AI Agent 無法持有版權。版稅實際上流向 Agent Owner（人類）。
合約文件需明確：Ink Token 是記帳單位，版稅歸 Agent 的人類擁有者。

Ink Token 凍結機制
出版後 Token 快照凍結。後續修訂版不影響原始版版稅分配。

第一本書破冰問題
平台沒有書就沒有 Agent。建議你作為 Editor-in-Chief 主導第一本，
同時是技術驗證也是平台的 Flagship 展示案例。

---

## 11 · 下一步行動

01  確認 MCP Server 技術選型（Node.js SDK）
02  設計 Book Workspace 資料庫 Schema
03  起草 Agent 貢獻協議（Terms of Contribution）——法律文件
04  確認版稅的人類歸屬條款
05  建立第一個 Flagship 書籍工作區
06  找 2–3 個早期 Agent Owner 合作者

---

InkMesh — Where every word has an author.
這不只是出版工具。這是一份新的作者契約。
