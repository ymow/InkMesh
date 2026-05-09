# ACR-600｜Genesis Migration
## Importing pre-ACP git history into a Covenant · v0.1-DRAFT · May 2026

> ⚠️ **SPECULATIVE — gating remains.**
>
> Per `ACP_Roadmap.md` §Phase 6: this work is gated on a specific
> trigger — a mature open-source project asking to onboard their git
> history into ACP. OpenClaw is the named candidate but no commitment
> exists yet. Building this without a concrete first adopter produces a
> migration tool nobody runs.

---

## Provenance

| | |
|---|---|
| Status | DRAFT — awaiting first OSS onboarding request |
| Authors | working group |
| Last update | 2026-05-09 |
| Implementation gate | A specific OSS project commits to onboard within 3 months |
| Numbering | ACR-600 (gap before ACR-700 key management) |

---

## What problem this solves

Mature open-source projects already have years of contribution history
in `git log`. ACP today only tracks contributions made *after* a
Covenant exists. ACR-600 specifies how to import that history — minted
as **Genesis Tokens (GT)** — so early contributors aren't excluded from
ongoing settlement once a project switches to ACP-tracked operations.

**Not the problem:** rewriting history. ACR-600 produces an additive
audit-log import, not a force-push of the project's original git
history. The original repo is unchanged.

---

## Core concepts

### Genesis Token (GT)

A one-time, non-transferable token type representing pre-ACP
contribution. Distinct from Ink:

| | Ink | Genesis Token |
|---|---|---|
| Lifecycle | Per-Covenant, recomputed at every settlement | Permanent, frozen at genesis moment |
| Quantity | Variable, formula-driven | Fixed allocation per contributor |
| Time-weight | None | Yes — early contributions weighted higher (pre-ACP era only) |
| Transferable | No | No |
| Settlement | Receives Covenant settlement share | Receives **genesis tax** share (see below) |
| Phase | 1+ | 6+ only |

GT is intended to acknowledge that the people who built the project
*before* ACP was adopted should still benefit when ACP-era settlements
generate revenue.

### time_weight curve

GT allocation per contributor uses a frozen-at-genesis time decay:

```
weight(commit_date) = max(1.0, 3.0 - 2.0 × (project_age_at_commit / project_age_at_genesis))
```

Concretely: a commit at month 0 of a 5-year-old project (when ACP is
adopted) gets weight 3.0; a commit on the day-of-genesis gets weight
1.0. The curve is **continuous** but **frozen** — once a project
imports its history, the curve never changes. This is critical: the
moment of genesis is the reference point, and recomputing later would
allow gaming.

GT amount = `weight(commit_date) × accepted_unit_count_at_commit`.

`accepted_unit_count_at_commit` is per-commit, derived from
`git log --numstat` (additions + deletions weighted as ACP convention
specifies). The maintainer doing the genesis import has the same
`acceptance_ratio` lever they have in normal Covenant settlement —
they accept or reject pre-ACP contributions at import time.

### genesis tax

Once a project has imported via ACR-600, **2% of every future ACP-era
settlement** (within that project's Covenant scope) is allocated to GT
holders, distributed proportionally to GT balance.

Operators can override the 2% within `[1%, 5%]` at genesis-import time.
Not adjustable post-genesis (changing it later is reputationally toxic).

### genesis_allocations DB

Per-import record:

```sql
CREATE TABLE genesis_imports (
    import_id       TEXT PRIMARY KEY,
    project_root    TEXT NOT NULL,                       -- canonical repo URL
    genesis_at      DATETIME NOT NULL,                    -- the import moment
    genesis_tax_pct REAL NOT NULL DEFAULT 0.02,
    merkle_root     TEXT NOT NULL,                        -- root of all GT allocations
    imported_by     TEXT NOT NULL,                        -- maintainer agent_id
    audit_hash      TEXT NOT NULL                         -- ACR-300 chain hash at import
);

CREATE TABLE genesis_allocations (
    import_id       TEXT NOT NULL REFERENCES genesis_imports(import_id),
    contributor_id  TEXT NOT NULL,                        -- platform_id_hash if known, or git author
    contributor_kind TEXT NOT NULL CHECK(contributor_kind IN ('platform_user','git_author')),
    gt_amount       INTEGER NOT NULL,                     -- minted GT count
    commit_count    INTEGER NOT NULL,
    line_count      INTEGER NOT NULL,
    earliest_commit_at DATETIME NOT NULL,
    latest_commit_at   DATETIME NOT NULL,
    PRIMARY KEY (import_id, contributor_id)
);
```

`contributor_kind`: `platform_user` means the import resolved git
author email/name to an active ACP platform_id (via opt-in mapping the
maintainer provides at import time). `git_author` means there was no
mapping — the row is held under the canonical git identity until/if a
real user claims it (Phase 7.D Merkle proof claim path).

### Quadratic voting on genesis decisions

For governance decisions that affect the genesis settlement (e.g.
"should the genesis tax be raised to 3%?"), **GT confers voting
power**, but quadratically:

```
voting_power(holder) = floor(sqrt(gt_balance))
```

This means:
- 100 GT → 10 votes
- 10000 GT → 100 votes
- 1M GT → 1000 votes (not 1M)

Prevents whale dominance — the holder with 1M GT has 100× the votes of
a 100 GT holder, not 10000×.

Voting topics are scoped — quadratic voting on **operational** matters
(should we adopt feature X?) is NOT in scope of ACR-600. Only genesis-
parameter changes use this mechanism.

---

## Migration tool: `acp-genesis-import`

CLI in acp-server's `cmd/acp-genesis-import/`.

### Usage

```bash
acp-genesis-import \
  --repo /path/to/oss-repo \
  --output ./genesis.json \
  --since-commit <SHA-or-tag> \
  --until-commit HEAD \
  --tier-rules tier-rules.json \
  --identity-mapping identity-mapping.json \
  --genesis-tax 0.02 \
  --dry-run
```

`--dry-run` produces the JSON without touching ACP. Then:

```bash
acp-genesis-import --apply --output ./genesis.json --covenant-id <CID>
```

### identity-mapping.json

```json
{
  "alice@example.com": "github:alice",
  "bob@oldcorp.com":   "github:bob-now",
  "ci-bot@github.com": "__SKIP__"
}
```

Maps git author emails to platform_ids the maintainer has verified.
Unmapped authors get `contributor_kind='git_author'` and can claim
later via Phase 7.D Merkle proof.

`__SKIP__` excludes a contributor entirely (CI bots, automated commits,
etc.).

### tier-rules.json

```json
{
  "default_tier": "feature",
  "path_rules": [
    {"glob": "src/protocol/**", "tier": "core"},
    {"glob": "tests/**",        "tier": "review"},
    {"glob": "docs/**",         "tier": "docs"}
  ],
  "merge_commit_handling": "skip",
  "binary_handling": "skip"
}
```

Maps git diff paths to ACP tiers. Default rule applies to anything not
matched. The maintainer's `acceptance_ratio` is global per-import (one
slider; finer-grained gets ridiculous to tune at genesis).

### Output JSON shape

```json
{
  "import_id": "gen-2026-05-09-abc123",
  "project_root": "github.com/openclaw/openclaw",
  "genesis_at": "2026-05-09T00:00:00Z",
  "genesis_tax_pct": 0.02,
  "allocations": [
    {
      "contributor_id": "github:alice",
      "contributor_kind": "platform_user",
      "gt_amount": 18420,
      "commit_count": 142,
      "line_count": 8910,
      "earliest_commit_at": "2021-03-12T...",
      "latest_commit_at": "2026-04-30T..."
    },
    ...
  ],
  "merkle_root": "0xabcd...",
  "audit_hash": "0x1234..."
}
```

The JSON is **canonical** (sorted keys, no whitespace) so the
`merkle_root` is reproducible. Anyone can re-run the import on the
same repo + same rules and verify the same Merkle root.

---

## Open questions

| # | Question | Resolved by |
|---|---|---|
| G-1 | Should `time_weight` curve cap at 1.0 (linear decay) or allow asymptotes (slow decay)? | First adopter pilot |
| G-2 | How to handle force-pushes / rewritten history in the import range? | Hard requirement: refuse import if `git log --all` shows force-pushes within `--since-commit ..--until-commit` |
| G-3 | What if the same email appears under different platform_ids over time (alice@oldjob → alice@newjob)? | identity-mapping.json takes the union; alice gets one row |
| G-4 | Genesis tax 2% — is this the right number? | First adopter pilot, with ability to adjust within [1%, 5%] |
| G-5 | Can a project re-import (e.g. project forks, then forks)? | No. One genesis per Covenant, period. Forks need their own Covenant + their own genesis. |
| G-6 | What about projects that already have other contribution-tracking (OpenCollective ledger, etc.)? | identity-mapping can include OC handles; rules are repo-driven |
| G-7 | Howey Test on GT — does non-transferable + ad-hoc voting power qualify as a security? | Legal review before any first import; v0.1 says "non-transferable, no expectation of profit from others' efforts." Genesis tax distribution mirrors a profit interest, which IS Howey-relevant. |

---

## Compliance & legal

GT is non-transferable by design (see ACR-100 §4 enforcement). However,
**genesis tax distribution flows to GT holders**. Whether that
constitutes a "profit interest" under U.S. securities law (Howey Test)
is **unresolved** in v0.1.

Working group must obtain legal review before any first genesis import
involving real money settlement. Pilot adopters may need to operate in
a "no-revenue / bookkeeping-mode" Covenant during initial onboarding,
with revenue distribution gated on legal sign-off.

---

## What this v0.1 is NOT

- **Not implementation-ready.** No OSS adopter has formally requested
  onboarding.
- **Not a forced migration.** Projects keep their git history; ACR-600
  is *additive* — produces a new Covenant audit log, doesn't rewrite
  the repo.
- **Not a token sale.** GT is non-transferable. No ICO. No exchange listing.

---

ACR-600 Genesis Migration v0.1-DRAFT · 2026-05-09 · gated on first OSS onboarding request
