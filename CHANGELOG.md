# Changelog

All notable changes. Format: [Keep a Changelog](https://keepachangelog.com/); versioning: SemVer.

## [Unreleased]

## [1.5.0] - 2026-11-12

### Added

- 日常记账新增 `bookkeep.py`，用已有 issue URL 入板、补字段并读回，确认后关闭。中断可用同一 URL 续跑（#29）。

### Fixed

- 对账按 issue 编号定位，旧账本仅在标题唯一时匹配。批量填字段遍历全部分页，写入后读回核验（#27）。
- 接入优先复用仓库登记的 Project 编号，保留已有 Status 和视图。本地模板激活支持 Linux 和 macOS，文件注入使用读取时的 SHA 防止覆盖并发编辑（#27、#31）。
- 验收表单列未填工时，区分空值与 0h。GitHub 文本以纯文本写入 Excel（#31）。
- GitHub 读取按响应头退避。批量写入结果不确定时停止，重跑先读回再补差异（#31）。

### Documentation

- 同步中英文快速上手、接入、续跑和导出说明，更新新版 `gh` 的字段寻址及限流重试指引（#25、#26、#31）。

## [1.4.0] - 2026-11-10
### Fixed
- `new-project.sh`: 坑6 升级地雷——Status 选项已一致时跳过 `updateProjectV2Field` 重交（实测重交会清空全部条目已选值,升级有数据的仓库必踩；沙盒复现验证）
### Added
- `new-project.sh` 注入 AGENTS.md 小节（Codex 等读 AGENTS.md 的工具入口；与 CLAUDE.md 共用 `merge_section` 小节级幂等合并）；`install.sh` 建兼容软链 `~/devledger`；模板路径统一为标准安装路径 `~/.agents/skills/devledger`（他人机器引用不再断裂）
### Docs
- README 中英加 Mermaid 架构图与记账三步流程图；修快速上手路径残留与旧坑数
- SKILL.md/README 中英同步 6 字段/View 9 列/10 坑口径；补批量接入多仓库说明；example-ledger 补需求人；`.gitignore`；export 清理死代码
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
