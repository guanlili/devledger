# Changelog

All notable changes. Format: [Keep a Changelog](https://keepachangelog.com/); versioning: SemVer.

## [Unreleased]
### Docs
- 坑3 补次级限流实测细节（触发阈值/冷却期 GraphQL 读写全封/重试续窗口/REST 可用/批量写策略）——2026-11-09 回填实战沉淀
### Fixed
- `new-project.sh`: 重跑幂等三连修——mkfield 去重改走 `gql()` 带重试直查（次级限流时查询失败≠字段不存在，绝不落入创建分支 + id 形状校验）；CLAUDE.md 注入幂等标记改用小节标题（v1.2.1 模板正文无 URL，旧标记失效会重复追加小节）；`put_file` 一致性判断改整串相等（子串包含会把「去重后的新内容是旧文件前缀」误判为已存在）

## [1.3.0] - 2026-11-09
### Added
- `fill-field.py`: bulk field fill with built-in read-back verification (plan → fill only drift → re-sweep), idempotent re-runs; `--where FIELD=VALUE` filter, `--dry-run`
- `_common.py`: shared rate-limit-aware gh runner + GraphQL wrapper + value normalization (single point of policy; reconcile/export refactored onto it)
- Tests for fill-field planning logic (norm-aware idempotency)

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
