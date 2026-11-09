# Changelog

All notable changes. Format: [Keep a Changelog](https://keepachangelog.com/); versioning: SemVer.

## [1.2.1] - 2026-11-09
### Fixed
- `reconcile`: normalize numeric/string field values before comparison — data files may write `2` / `2.0` / `"2"` interchangeably without false-positive DRIFT (#6)

## [1.2.0] - 2026-11-09
### Added
- `demo.sh`: 2-minute end-to-end demo (sandbox repo → onboarding → 2 ledger entries → timesheet export)
- `install.sh`: install/update/doctor unified — one idempotent command, re-run anytime
- `new-project.sh`: same-name Project dedup (safe re-runs)
### Fixed
- API injection `PM_DIR` path bug; placeholder dual-replacement + assertion

## [1.1.0] - 2026-11-09
### Added
- Issue template: decision context (why now / rejected alternatives) and Verification section
### Fixed
- API injection placeholder mismatch (`__PM_PROJECT__` vs `{PJ_NUM}` eras)

## [1.0.0] - 2026-11-09
### Initial public release
- Agent-Skills-compliant skill (SKILL.md / AGENTS.md / scripts / references / assets)
- Bilingual README (English default + 简体中文), MIT license, sanitized git history
- Dogfooding ledger: devledger tracks its own development (public Project)
