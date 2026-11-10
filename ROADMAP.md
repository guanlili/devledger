# Roadmap

**North star**: be the best practice (and reference implementation) of the **1+N paradigm** — one tech lead + a swarm of AI agents — where every unit of delegated work is booked with evidence, hours, and decision context. We are NOT building a Jira alternative.

## The four laws (product constitution)

1. **Judgment is never delegated** — what/why/acceptance stay human; how is fully delegated
2. **Execution must self-report** — a session that didn't bookkeep equals work that didn't happen
3. **One source of truth** — issues are the ledger; everything else is a derived view
4. **Hours are the metric** — human-equivalent hours measure whether a delegation was worth it

Every feature decision is tested against these laws.

## Now (v1.2.x): wait for the first stranger

Nothing to build — infrastructure is complete. The task is visibility: awesome-claude-skills / Agent Skills directories / V2EX / r/github / X. The pitch writes itself: *the tool that keeps its own construction ledger with itself*.

## Signal-triggered evolution

| Signal | Unlocks |
|---|---|
| Real usage feedback | Effect screenshots, social preview, ShellCheck → blocking, release automation |
| A second maintainer | Governance upgrade (CODEOWNERS, review rotation) |
| "How do I aggregate projects?" | Multi-project export (`--project` multi-value) |
| A second round-based customer | Revive delivery-rounds / acceptance mode (tools are dormant, not deleted) |
| "What did we do this month?" | Captain's monthly report |
| Official Agent Skills directories emerge | Submit immediately |
| Big multi-module repo / multiple PMs | Ledger boundary follows delivery boundary, not repo: module labels → multi-Project per repo → org-level Projects (needs `--owner <org>` support). 1+N scales as a federation of fleets |
| Captain dashboard questions (weekly digest, defect ratio, per-session stats) | Wake the aggregation views — the tech lead's dashboard is a paradigm core, not a nice-to-have |

## Never (anti-roadmap)

- **No Jira features** — scheduling, assignment, multi-human approval flows solve problems that don't exist in 1+N
- **No wall-clock tracking** — human-equivalent hours only; auto-timing turns a ledger into surveillance and changes what the tool is
- **No feature chasing** — every new field or ritual must answer "who consumes this?" (we once deleted our own priority field for failing this test)
- **No productized backfill/migration tooling** — old-ledger migration is rare (one-off per project, mostly at adoption); the manual pattern in methodology.md plus battle notes in pitfalls suffice. Decided 2026-11-10 after the energy-platform Feishu migration: worth recording, not worth building

## Endgame

Accounting and valuation of AI-assisted delivery is an open industry question — no native support anywhere, commercial tools still on manual timers. If devledger accumulates enough real cases, it can become a reference practice for the conversation, maybe the conversation itself.
