# Contributing to devledger

Thanks for improving the ledger! 📗

## Setup

```bash
git clone https://github.com/guanlili/devledger.git && cd devledger
python3 -m unittest discover -s tests    # all green before you start
```

`scripts/install.sh` is optional for contributors — it targets end-user machines.

## Map

- `SKILL.md` — agent entry point (read this first)
- `scripts/` — the tools; `references/` — deep docs; `assets/` — templates
- `tests/` — unit tests (CI runs them on every PR)

## Conventions

- **Commits**: `type(scope): message` — e.g. `fix(reconcile): normalize numbers (#6)`. Append `(#N)` when the change belongs to a ledger issue.
- **PRs**: describe *why now*, *alternatives considered*, and *how you verified* — mirror the decision-context style of our issue template. Evidence-first.
- **Bug fixes**: add/extend a unit test that fails before your fix and passes after (see `tests/test_reconcile_norm.py` for style).
- **Language**: English or 简体中文, both welcome.

## Ledger note

Maintainers bookkeep all merged work in the [project ledger](https://github.com/users/guanlili/projects/13) (hours tracked automatically — external contributors don't need ledger access). Community contributions are recorded with source `社区`.
