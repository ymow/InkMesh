# ACR-530｜On-Chain Merkle Proof
## Trustless settlement verification + GT claim path · v0.1-DRAFT · May 2026

> ⚠️ **SPECULATIVE — gating remains.**
>
> Per `ACP_Roadmap.md` §Phase 7.D: this work is gated on Phase 7.A
> (Escrow + Auto-Settlement, ACR-500) shipping AND ≥30 real settled
> Covenants AND a working ACR-510 multi-rail. Trustless verification
> is the **last** layer added — only meaningful when the layers below
> are real.

---

## Provenance

| | |
|---|---|
| Status | DRAFT — awaiting Phases 7.A, 7.B, 7.C operational maturity |
| Authors | working group |
| Last update | 2026-05-09 |
| Implementation gate | Phase 7.A live + ≥30 real settlements + ACR-510 ≥1 rail beyond v1 |
| Numbering | ACR-530 (Phase 7.D extension; final piece of the Layer 3 trust hierarchy) |

---

## What problem this solves

Layer 1 (hash chain, ACR-300) requires trusting the server has not
replaced the entire chain. Layer 2 (git anchor, ACR-400) requires
trusting that the git remote hasn't been force-pushed. Both are
real-world reasonable but not **trustless**.

ACR-530 specifies how settlement Merkle roots get published to a
public blockchain, making verification:

- **Server-independent** — anyone with the Merkle proof can verify
- **Trustless** — only requires trusting the chain itself
- **Permissionless** — no operator gatekeeping verification queries
- **Persistent** — verification works even if the original acp-server
  is gone

ACR-530 also specifies the **GT claim path**: how Genesis Token
holders (per ACR-600) prove their entitlement on-chain to claim their
share of the genesis-tax pool, without needing the original genesis
import to remain online.

---

## Core concepts

### Settlement Merkle root

At each Covenant settlement (`confirm_settlement_output`), acp-server:

```
1. Constructs a Merkle tree of all settlement leaves:
   each leaf = hash(participant_id || amount_minor || rail_tx_hash)
2. Computes the root.
3. Publishes the root on-chain via a single transaction
   to a published `ACPRegistry` contract.
4. Records the on-chain tx_hash in the audit log
   AND the git anchor (Layer 2) for cross-layer auditability.
```

The on-chain registry contract is a thin write-only ledger:

```solidity
// pseudocode
contract ACPRegistry {
    struct SettlementProof {
        bytes32 covenantId;
        bytes32 merkleRoot;
        uint256 settledAt;
        address publisher;  // server's signing address
    }

    mapping(bytes32 => SettlementProof) public settlements;
    event Settlement(bytes32 indexed covenantId, bytes32 merkleRoot);

    function publish(bytes32 covenantId, bytes32 merkleRoot) external {
        require(settlements[covenantId].covenantId == 0, "already settled");
        settlements[covenantId] = SettlementProof(
            covenantId, merkleRoot, block.timestamp, msg.sender
        );
        emit Settlement(covenantId, merkleRoot);
    }
}
```

Once published, the Merkle root is immutable. Anyone can verify a
specific participant's share by:

```
participantLeaf = hash(participant_id || amount_minor || tx_hash)
proof = [hash1, hash2, ...]  // siblings up to root
verify(merkleRoot, participantLeaf, proof) == true
```

### GT Merkle proof claim

Genesis Tokens (per ACR-600) are minted at import time. The genesis
import produces:

```json
{
  "import_id": "gen-...",
  "merkle_root": "0xabcd...",
  "allocations": [...]
}
```

That `merkle_root` is published on-chain via a separate
`ACPGenesisRegistry` contract. Each GT holder can later **claim** their
GT entitlement on-chain by proving inclusion in the tree:

```
GT holder calls:
  ACPGenesisRegistry.claim(
    importId,
    contributorIdHash,
    gtAmount,
    proof[]
  )

Contract verifies:
  hash(contributorIdHash || gtAmount) ∈ merkleTree(merkleRoot)

If yes:
  contract mints/transfers the holder's GT-share-of-the-pool
  to their wallet, marks claim as fulfilled.
```

This makes GT claims **server-independent**. Even if every acp-server
hosting the original Covenant goes offline, the Merkle proof in the
contract enables permissionless claiming.

### Dispute resolution (on-chain arbitration sketch)

When a Settlement is published to ACPRegistry, a **challenge window**
(default 7 days) opens. During this window:

```
Anyone can submit:
  ACPRegistry.challenge(
    covenantId,
    counterRoot,         // their alternative Merkle root
    counterEvidence      // off-chain link to evidence
  )

If a challenge is filed:
  Settlement enters DISPUTED state on-chain.
  Owner has N days to respond with evidence.
  An arbitrator (could be DAO-elected, see ACR-600 quadratic voting,
    or off-chain Kleros-style oracle) decides.
  Loser pays gas + penalty.
```

ACR-530 does NOT specify the arbitrator mechanism in v0.1 — that's its
own ACR (probably ACR-540). v0.1 only specifies the **challenge
schema** so future arbitration can plug in.

---

## Schema additions (informative)

```sql
CREATE TABLE settlement_onchain_anchors (
    covenant_id     TEXT PRIMARY KEY REFERENCES covenants(id),
    merkle_root     TEXT NOT NULL,                    -- 0x... hex
    chain_id        INTEGER NOT NULL,                 -- e.g. 8453 = Base mainnet
    contract_address TEXT NOT NULL,
    publish_tx_hash TEXT NOT NULL,
    publish_block   INTEGER NOT NULL,
    publish_at      DATETIME NOT NULL,
    challenge_state TEXT NOT NULL DEFAULT 'OK'
                    CHECK(challenge_state IN ('OK','DISPUTED','RESOLVED_OWNER','RESOLVED_CHALLENGER'))
);

CREATE TABLE merkle_leaves (
    covenant_id     TEXT NOT NULL REFERENCES covenants(id),
    leaf_index      INTEGER NOT NULL,
    leaf_hash       TEXT NOT NULL,
    leaf_data       TEXT NOT NULL,                    -- JSON: {participant_id, amount_minor, tx_hash}
    proof_path      TEXT NOT NULL,                    -- JSON array of sibling hashes
    PRIMARY KEY (covenant_id, leaf_index)
);

CREATE TABLE genesis_onchain_anchors (
    import_id       TEXT PRIMARY KEY REFERENCES genesis_imports(import_id),
    merkle_root     TEXT NOT NULL,
    chain_id        INTEGER NOT NULL,
    contract_address TEXT NOT NULL,
    publish_tx_hash TEXT NOT NULL,
    publish_at      DATETIME NOT NULL
);
```

---

## Tool surface

| Tool | Purpose | Auth |
|---|---|---|
| `publish_merkle_root` | Auto-called during settlement; idempotent | System |
| `get_merkle_proof` | Returns the proof path for a participant | Member / public |
| `verify_settlement` | Verifies a (root, leaf, proof) tuple | Public, off-chain available |
| `challenge_settlement` | On-chain only; no acp-server tool needed | (chain participants) |
| `claim_genesis_token` | On-chain only via ACPGenesisRegistry | (chain participants) |

---

## Open questions

| # | Question | Why |
|---|---|---|
| OC-1 | Which chain(s) for the registry contract? | Base, Optimism, Arbitrum, Ethereum mainnet — gas vs. trust trade-off |
| OC-2 | Should the contract support upgradeability? | Trade-off: adaptability vs. immutability promise |
| OC-3 | Who pays the on-chain publishing cost? | Owner? Built into settlement gas budget? Operator? |
| OC-4 | Challenge window length: 7 days fixed, or per-Covenant? | 7d works for most; high-stakes Covenants might want 30d |
| OC-5 | What's the evidence format for `challenge`? | IPFS hash? Direct on-chain calldata? Both? |
| OC-6 | Cross-chain settlements (Covenant on Base, claim on Optimism)? | Probably out of scope for v0.1 |
| OC-7 | Privacy: Merkle leaves expose participant identities | participant_id hash is fine; but amount is exposed. Tradeoffs? |
| OC-8 | Can a Covenant opt OUT of on-chain anchoring after first settlement? | Probably no — but what about during DRAFT? |

---

## Failure modes

### F-1: Chain RPC outage during publish

acp-server retries with exponential backoff (1s, 2s, 4s, ...). If
RPC is unreachable for >1 hour, settlement is marked
`SETTLED_LOCALLY_PENDING_ANCHOR` and the audit log contains the
outstanding state. Operators can manually re-publish later via
`publish_merkle_root --force` once chain access restores.

### F-2: Contract upgrade breaks compatibility

If `ACPRegistry` is non-upgradeable (preferred per OC-2), this
doesn't happen. If it IS upgradeable, settlements published before
upgrade must remain readable post-upgrade — enforced by working group
discipline + audit, not by code.

### F-3: Gas spike makes publish prohibitively expensive

Operator can defer publishing for hours/days. Audit log marks the
deferral. If the deferral exceeds 7 days, ACR-530 considers it a
**violation** of trust assumptions — Covenant settlement is then
stuck at Layer 2 (git anchor) trust level. Document publicly in
release notes.

### F-4: Merkle root collision

Hash function (SHA-256 or keccak256) is collision-resistant by
assumption. v0.1 does not specify which; both are fine for the
forthcoming threat model. Choice of hash is OC-9 (added to list).

---

## Anti-patterns

1. **Don't publish Merkle roots as a marketing exercise.** Each
   publish costs gas and introduces challenge-window operational
   work. Only publish on real settlements.
2. **Don't store full settlement data on-chain.** Only the root +
   minimal metadata. Storing full audit logs on-chain is prohibitively
   expensive AND a privacy leak (participant_ids would be public).
3. **Don't mutate the Merkle tree after publishing.** Append-only is
   the protocol's invariant. New settlements get new roots; old
   roots are sacred.

---

## What this v0.1 is NOT

- **Not implementation-ready.** Multiple gates ahead.
- **Not a complete dispute-resolution mechanism.** ACR-540 (or whatever
  arbitrator-selection ACR comes next) handles that.
- **Not a token to be minted.** ACPRegistry stores roots, doesn't
  issue ERC-20s on the contract level.

---

ACR-530 On-Chain Merkle Proof v0.1-DRAFT · 2026-05-09 · gated on Phase 7.A live + ≥30 settlements
