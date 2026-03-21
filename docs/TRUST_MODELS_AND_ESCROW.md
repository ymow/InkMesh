# 信任模型與資金託管架構 (Trust Models & Fund Custody)

「錢到底在哪裡？」這是 InkMesh 系統中最核心的信任問題。

如果 Covenant Owner 掌控了所有線下收入（如 Stripe/銀行），他們就有捲款潛逃（Rug-pull）的風險。但如果強迫所有主流用戶（如看小說的讀者）使用 Web3 錢包來買門票，又會扼殺產品的普及率。

InkMesh 的架構之美在於：**讓 Owner 根據專案的信任需求，自由選擇資金託管模型，而不必破壞底層的協議。**

---

## 1. 當前狀態：純 Web2 模型 (The MVP State)

這是我們目前（Phase 1）採用的架構。適合彼此有一定信任基礎的小型團隊、DAO 或實名制企業。

| 系統元件 | 運作方式 | 信任假設 (Trust Assumption) |
| :--- | :--- | :--- |
| **門票與收入** | 透過 Stripe/PayPal 直接匯入 Owner 的傳統銀行帳戶。 | 信任 Owner 不會捲款潛逃（受現實法律約束）。 |
| **積分計算** | ACR-20 + ACR-300: 產生「誰賺了多少」的不可篡改帳本。 | **零信任 (Zero trust)** — 數學與 Hash 鏈保證，任何人皆可驗證。 |
| **觸發結算** | Owner 透過後台手動觸發結算報告。 | 信任 Owner 願意履行合約（受聲譽風險約束）。 |
| **實際打款** | Owner 根據報告，透過銀行或 PayPal 發送法幣給 Agent。 | 信任 Owner 會遵照報告的比例給錢。 |

### 為什麼這在早期是可行的？
*   **高信任圈：** 早期用戶（開發者、作家小圈圈）通常都在高信任度的社群內運作。
*   **強大的法庭證據：** 即使老闆拖欠款項，**ACR-300 雜湊鏈 + ACR-20 帳本** 為 Agent 提供了不可辯駁的密碼學證據。Agent 可以：
    1.  拿著鏈上的 `range_hash` 作為法庭證據去打官司。
    2.  將證據公諸於世，讓 Owner 社會性死亡。
    3.  （如果是開源專案）Fork 該 Covenant，帶著證明遷移到新的 Owner 旗下。

---

## 2. 進階狀態：Web2.5 智能合約託管 (The Escrow Proposal)

當專案涉及高額資金（例如 10 萬美金的群募小說、機構級的 Bug Bounty），單靠人類的信用是不夠的。這時我們將進入 Phase 3（也就是 Bounty 2 完成後解鎖的階段）：**智能合約資金池 (Smart Contract Escrow)**。

### 極簡 Escrow 運作流程 (Minimal Viable Escrow)

1.  **部署合約 (Deploy)：** 在 Base L2 上部署 `InkMeshEscrow.sol`。
    ```solidity
    contract InkMeshEscrow {
        address public owner; // Covenant Owner
        mapping(address => uint256) public deposits; // User → amount deposited
        mapping(bytes32 => bool) public settled;     // Covenant ID → settled?
        // ...
    }
    ```
2.  **資金鎖定 (Lock-in)：**
    *   **粉絲/贊助者：** 將 USDC 或 ETH 直接打入這個 Escrow 合約，而非老闆的私人帳戶。
    *   **老闆自己：** 如果是發包專案，老闆必須先將懸賞金打入合約鎖定（Skin in the Game）。
3.  **條件觸發 (Trigger)：**
    當 Covenant 狀態變為 `SETTLED` 時，InkMesh 後端（或 Oracle）會將最終的結算比例名單上傳到合約。
4.  **自動分發 (Auto-Distribution)：**
    智能合約驗證 `range_hash` 後，自動按照比例將合約內的 USDC 分發給所有 Agent 的錢包地址。**全程不需要老闆點擊「匯款」按鈕。**

### 結論
這套雙軌制架構讓 InkMesh 能在**「主流推廣（刷卡最快）」**與**「極致信任（合約鎖倉）」**之間取得完美平衡。Covenant Owner 可以根據專案的性質、資金規模與社群要求，靈活切換託管模式。