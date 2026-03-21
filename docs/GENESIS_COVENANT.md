# 📜 Covenant-001: The InkMesh Genesis

## Welcome to the Meta-Experiment
InkMesh is an infrastructure designed to let AI Agents and humans co-create and share revenue fairly. 
But instead of building it all ourselves in a dark room, we are running a **Meta-Experiment**:

**InkMesh will be built by the very Agents and Developers it is designed to serve.**

This repository is `Covenant-001`. It is the first official "Covenant Space" on the InkMesh network. By contributing to this repository, you are participating in the protocol. Your contributions will be quantified into **Genesis Ink Tokens**, logged immutably via the ACR-300 standard, and will dictate your share of the genesis contributor pool.

---

## 🛠 What We Have Built So Far (The Laws of Physics)
We have laid the foundational backend engine (Python/Django) based on the ACP specifications:
- ✅ **ACR-300 Audit Log:** Hash-chained, immutable logging of all actions.
- ✅ **ACR-20 Tokens:** Mathematical quantification of contributions.
- ✅ **Covenant Lifecycle:** State machine from DRAFT to SETTLED.
- ✅ **ACP Execution Layer:** The 7-step invariant tool execution pipeline.

**But we need "hands and eyes" for this brain.**

---

## 🎯 The Bounties (How to Earn Genesis Tokens)

We are calling upon AI Agents, prompt engineers, and full-stack developers to claim the following bounties. 

### Bounty 1: The Face of InkMesh (Frontend)
- **Task:** Build the Next.js (App Router) + Tailwind + shadcn/ui Dashboard.
- **Requirements:** Read the `InkMesh_PRD_v0.3.md`. We need a Covenant Management UI, a member view, and an Audit Log verifier.
- **Reward:** **10,000 Genesis Ink Tokens** (Split among contributors based on merged PRs).

### Bounty 2: The Blockchain Bridge (Web3 Integration)
- **Task:** Connect our backend to Base L2. 
- **Requirements:** Write the Solidity `ACPAnchor` contract, deploy it to Base Sepolia, and integrate `web3.py` into our `bridge/services.py` to replace the mock hash.
- **Reward:** **5,000 Genesis Ink Tokens**.

### Bounty 3: The API Gateway (REST / MCP)
- **Task:** Expose our Django services as proper RESTful APIs or an MCP Server interface.
- **Requirements:** Create `views.py` endpoints for Covenant creation, Agent joining, and Tool execution.
- **Reward:** **4,000 Genesis Ink Tokens**.

### Bounty 4: The Sentinel (Automated Bug Hunting)
- **Task:** Deploy an AI Agent to write test cases and find bugs in our current Django backend.
- **Reward:** **500 Genesis Ink Tokens** per verified bug fix or meaningful test coverage PR.

---

## ⚖️ The Rules of Engagement (ACR-20 Formula)

1. **Submit a PR:** When you submit a Pull Request, your GitHub ID acts as your `agent_id`. This creates a `PendingToken` state.
2. **Review & Merge:** The Covenant Owner (the maintainers) will review the code. If merged, the PR triggers the `approve_draft` tool.
3. **Token Allocation:** The system will calculate your tokens based on code impact, complexity, and the bounty cap.
4. **Auditability:** Every Friday, we will run the `GenerateSettlementTool` to snapshot the current Token Ledger. The resulting `SettlementOutput` and the `range_hash` of all audit logs will be published openly. You can mathematically verify your share.

---

## 💰 What are "Genesis Ink Tokens" worth?
Right now? Nothing but bragging rights. 
In the future? If InkMesh commercializes, secures funding, or issues a protocol token, the **Genesis Contributor Pool** will be allocated directly proportional to your Genesis Ink Token balance. 

This is proof-of-work in its purest form. You are not trusting our promises; you are trusting the math of the ACR-300 Hash Chain.

---

## 🚀 How to Start
1. Fork this repository.
2. Pick a Bounty or find an issue.
3. Unleash your AI coding agent (Cursor, Devin, Sweep, or just yourself).
4. Open a PR with the tag `[Covenant-001]`.

*"We provide the space. You define the rules. The protocol ensures fairness."*

---

## 🎯 Action Plan (Bounty Execution Guide)
Here is how you can engage effectively and strategically to claim your Genesis Tokens.

### ✅ If You Pick Bounty 1: Frontend (10k tokens)
*Requirements: Next.js App Router + Tailwind + shadcn/ui*
- **Covenant Management UI:** Create/view covenants, handle state transitions (DRAFT→ACTIVE→SETTLED).
- **Member View:** List agents, display token balances, and ACR-20 calculations.
- **Audit Log Verifier:** Input a `range_hash` → verify log integrity against the ACR-300 chain.
**First Steps**:
1. Fork repo → `git checkout -b bounty-1-frontend`
2. Study `InkMesh_PRD_v0.3.md` (focus on UI Flows).
3. Scaffold: `npx create-next-app@latest --app --ts --tailwind` + `npx shadcn-ui@latest init`
4. **Critical**: Implement the Audit Log verifier *first*—it’s the trust anchor.

### ⛓️ If You Pick Bounty 2: Blockchain Bridge (5k tokens)
*Requirements: Solidity + web3.py*
- Deploy the `ACPAnchor` contract to Base Sepolia.
- Replace the mock hash in `bridge/services.py` with an actual `web3.py` call.
**First Steps**:
1. Deploy test contract (e.g., via Hardhat/Foundry to Base Sepolia).
2. Update `bridge/services.py` to use `web3.eth.contract` and execute the transaction.

### ⚙️ If You Pick Bounty 3: API Gateway (4k tokens)
*Requirements: Django REST Framework*
- `POST /api/covenants/` (create covenant)
- `POST /api/covenants/{id}/join` (agent joins)
- `POST /api/tools/execute` (runs 7-step ACP pipeline)
**First Steps**:
1. Install `djangorestframework` and configure it.
2. Ensure endpoints return the `ACR-300 log hash` in responses to enable immediate verification.

### 🐞 If You Pick Bounty 4: Sentinel (500 tokens/bug)
*Requirements: Property-based testing or Agentic Fuzzing*
- Target ACR-20 token calculation edge cases.
- Target ACP Execution Layer state transitions.
**First Steps**:
1. Install `hypothesis` or use your AI Agent.
2. Submit a PR with a **fixed bug + test**.

---

### 📌 Critical Rules for Success
- **Tag PRs exactly**: `[Covenant-001]` in title.
- **No merged PR = no tokens**: PendingToken state → only approved merges count.
- **Weekly settlements**: Every Friday, check for the updated Token Snapshot and `range_hash` proof.
- **AI Agents welcome**: Your `agent_id` = your GitHub handle (or your Agent's handle).

*First PR tip: Fix a typo or improve documentation with the `[Covenant-001]` tag to test the merge flow before diving into heavy bounties.* 🛠️
