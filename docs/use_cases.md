# InkMesh 跨領域 Use Cases (5 個情境)

InkMesh 的核心是「Covenant Space 協作基礎設施」。因為它把「做什麼」和「怎麼分潤」解耦了，所以它不只能用來寫書，還能用於任何需要**多方協作、量化貢獻、分配利益**的場景。

以下是 5 個不同領域的 Use Cases：

---

## Use Case 1: 開放原始碼專案贊助分配 (軟體開發 / Code)

**痛點：** 開源專案（如某個熱門的 npm 套件）收到企業贊助或 GitHub Sponsors 的錢，但 Maintainer 不知道該怎麼公平地分給其他幫忙解 Bug 的無名貢獻者。

*   **Covenant Owner:** 專案發起人 (Maintainer)
*   **Agent (創作者):** 社群開發者 (人類) 或自動修復 Bug 的 AI Agent (如 Sweep, Devin)
*   **遊戲規則 (Tier):**
    *   `Core Contributor` (Tier 倍率 1.5): 核心成員，提交 PR 積分加成。
    *   `Bounty Hunter` (Tier 倍率 1.0): 解決 Issue 的一般開發者。
*   **貢獻量化 (ACR-20):**
    *   **Tool:** `propose_commit` (提交 PR) / `approve_merge` (Merge PR)
    *   **Formula:** `(被 Merge 的程式碼行數 * 複雜度權重) * Tier 倍率`
*   **結算 (ACR-100):** 當專案收到一筆 USD 5,000 的贊助，Maintainer 點擊 `GenerateSettlementTool`。系統根據過去半年的「程式碼合併積分」，產出報告：AI Agent A 貢獻了 30% 代碼，分得 30%；人類開發者 B 分得 20%；Maintainer 保留 50%。

---

## Use Case 2: 虛擬偶像 (VTuber) 歌曲共創 (音樂製作 / Music)

**痛點：** 一首 VTuber 的原創曲需要作曲、作詞、編曲、混音、MV 繪師等多方參與。YouTube 收益或串流版稅下來後，常常因為口頭約定不清導致拆帳糾紛。

*   **Covenant Owner:** VTuber 經紀公司或獨立 VTuber 本人
*   **Agent (創作者):**
    *   音樂 AI Agent (如 Suno/Udio 生成片段)
    *   人類作詞家、人類繪師
*   **遊戲規則 (Tier & Tools):**
    *   **Tool:** `propose_track` (提交音軌/小節)、`propose_lyric` (提交歌詞)、`propose_asset` (提交 MV 素材)
*   **貢獻量化 (ACR-20):**
    *   不同 Tool 有不同的計分基礎。例如：被採用的主旋律給 1000 Token；一段副歌歌詞給 300 Token；一張 MV 插圖給 500 Token。
*   **結算 (ACR-100):** 歌曲在 Spotify 上架半年，收到版稅。經紀公司根據 Token 快照，精確地把錢依照當初約定好的 Token 佔比，分給作詞家、繪師，甚至如果有開發者寫了專屬的 AI 編曲 Agent，該開發者也能分到版稅。

---

## Use Case 3: 醫學/科學研究論文共筆 (學術研究 / Research)

**痛點：** 一篇醫學期刊論文通常有多個作者（First Author, Co-authors），大家對於誰做了多少實驗、寫了多少字、誰該掛什麼名次常常有爭議。

*   **Covenant Owner:** 實驗室主持人 (PI - Principal Investigator)
*   **Agent (創作者):** 博士生、研究助理、負責跑數據分析的 AI Data Agent
*   **遊戲規則 (Tier):**
    *   `Data Analyst` (倍率 1.0)
    *   `Literature Reviewer` (倍率 1.2)
*   **貢獻量化 (ACR-20):**
    *   **Tool:** `submit_experiment_result` (提交實驗數據)、`write_paragraph` (撰寫文獻回顧段落)。
    *   積分不是為了分錢（學術論文不一定有直接獎金），而是為了**「掛名順序 (Authorship)」**。
*   **結算 (ACR-100 變體):** 在此場景下，Settlement Output 不用於分美金，而是輸出一份**「不可竄改的貢獻度報告」**。這份報告可以直接附在論文後面交給期刊審查，以 Hash Chain 證明這篇論文確實是由這些人/Agent 合作完成，且貢獻比例清晰，解決學術倫理爭議。

---

## Use Case 4: 遊戲世界觀與劇本接龍 (遊戲開發 / Gaming)

**痛點：** 獨立遊戲團隊想製作一款擁有龐大世界觀的 RPG 遊戲，想要開放給社群玩家一起寫 NPC 的背景故事或支線任務，但無法承諾固定薪水。

*   **Covenant Owner:** 獨立遊戲工作室
*   **Agent (創作者):** 熱情玩家、專寫故事的 LLM Agents (如基於 Claude 訓練的敘事 Agent)
*   **遊戲規則 (Tools):**
    *   **Tool:** `propose_npc_lore` (提交 NPC 背景)、`propose_quest_line` (提交支線任務大綱)
*   **貢獻量化 (ACR-20):**
    *   如果玩家寫的任務被官方收錄進遊戲 (`approve_draft`)，玩家或該 Agent Owner 將獲得 Lore Token。
*   **結算 (ACR-100):** 遊戲在 Steam 發售並獲利後，工作室承諾將總營收的 10% 放入「社群貢獻池」。系統根據 Lore Token 結算，社群玩家根據自己的 Token 比例分得 Steam 營收的分紅。這是一種典型的 **"Create-to-Earn" (共創即賺錢)** 模式。

---

## Use Case 5: 律師事務所的法律合約模板庫 (專業服務 / Legal)

**痛點：** 律師事務所內部有多位律師，大家都會寫各種合約模板。如果某個律師寫的「股權轉讓協議模板」非常好用，其他律師拿去賣給客戶，原作者往往拿不到抽成，導致大家不願意把好東西分享到內部庫。

*   **Covenant Owner:** 律師事務所合夥人
*   **Agent (創作者):** 所內受僱律師、負責爬梳判例的 Legal AI Agent
*   **遊戲規則 (Tier):**
    *   空間類型為 `Template_Library` (自定義 SpaceType)
*   **貢獻量化 (ACR-20):**
    *   **Tool:** `submit_clause` (提交合約條款)、`update_clause` (根據最新法規更新條款)。
    *   **Formula (動態積分):** 每當其他律師下載/引用這個條款去服務客戶時，系統自動發給原作者 Token。這叫「被引用即得分」。
*   **結算 (ACR-100):** 每到年底分紅時，事務所根據 Token 快照，將一部分利潤分給那些「貢獻了最多高頻使用模板」的律師或 AI 工具開發者，激勵內部知識共享。

---

## 進階 Use Cases：入場券、付費門檻與人數限制 (Access Tiers)

InkMesh 的 `AccessTier` 系統允許 Covenant Owner 像經營俱樂部一樣經營協作空間。以下是三種結合「入場費 (Price)」與「人數限制 (Max Slots)」的進階玩法：

### Use Case 6: 高端付費共筆智庫 (付費入場 + Token 乘數加成)
**場景：** 華爾街的資深分析師發起一份「2027 AI 產業深度報告」，他只想要業內高手來共筆，不想要小白來洗版。
*   **入場費設定：** 
    *   `Pro Contributor` Tier：入場費 **$500 USD**，Token 倍率 **1.5x**。
    *   `Standard Contributor` Tier：入場費 **$50 USD**，Token 倍率 **1.0x**。
*   **機制：** 這種「Pay-to-Contribute（付費貢獻）」模式設立了極高的過濾門檻。付了 $500 的高手，因為有 1.5 倍加成，能在報告發售後分到更多的版稅。這保證了報告的超高品質，且過濾掉只會用低階腳本洗版的 Agent。

### Use Case 7: 封閉式黑客松 (免費入場 + 嚴格人數限制)
**場景：** 某公鏈基金會舉辦線上黑客松，開發一個 DeFi 協議。為了保證溝通效率與程式碼品質，他們只開放 20 個名額。
*   **入場費設定：**
    *   `Hacker` Tier：入場費 **$0 USD**，**限制 20 個名額 (Max Slots: 20)**。
*   **機制：** 名額先搶先贏，或是透過外部審核發放邀請碼。這 20 位開發者進入 Covenant 後，開始提交 PR。專案完成後，基金會直接根據這 20 人的 Ink Token 比例，瓜分總獎金池。

### Use Case 8: 粉絲經濟的「共創兼群募」 (付費旁觀 + 免費創作)
**場景：** 知名奇幻小說家準備寫續集，他邀請 5 位他最信任的「世界觀設定師（人類或 Agent）」來幫他擴充背景，同時開放給死忠粉絲付費「進場觀看」寫作過程。
*   **入場費設定：**
    *   `Lore Master` (創作者)：入場費 **$0 USD**，可以呼叫 `propose_passage` (有寫作權限)，**限制 5 個名額**。
    *   `VIP Reader` (旁觀者)：入場費 **$10 USD**，**名額無上限**，只能呼叫 `read_chapter` (只有閱讀權限，不能寫作，不能分潤)。
*   **機制：** 粉絲買入場券的錢（例如 10,000 個粉絲 = $100,000 USD）直接成為這個 Covenant 的「營收」。等書寫完後，老闆（小說家）和那 5 位 `Lore Master` 直接拿這筆十萬美金來進行結算分潤！這完美結合了「群眾募資」與「共創分潤」。

