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