# devledger

**The self-writing ledger for R&D management.** If it's not bookkept, it didn't happen.

devledger is a lightweight, [Agent Skills](https://agentskills.io)-compliant skill that turns AI development sessions into an automatic issue + hours ledger on GitHub Projects. You talk to your AI; when the session ends, the work is already recorded — with type, source, dates, and human-equivalent hours. At acceptance time, export a client-ready timesheet with one command.

## Why

- **Zero-input accounting**: no timesheets to fill, no boards to update. The AI records deliverables at session end — a hard rule, not a habit.
- **Evidence-first**: every ledger entry links real commits (`(#N)` convention) and verification results, with decision context captured while it's still fresh (why now, what alternatives were rejected).
- **Single source of truth**: issues are the ledger; Project fields and README summaries are derived views, rebuildable anytime via the reconcile tool.
- **One repo, one project**: Project name = repo name. Nothing to configure.

## Quick start

```bash
git clone git@github.com:guanlili/devledger.git ~/.agents/skills/devledger
bash ~/.agents/skills/devledger/scripts/install.sh          # idempotent self-check
~/devledger/scripts/new-project.sh <owner/repo>             # onboard any repo in one command
```

Daily loop: work with your AI as usual → session end auto-records the ledger.
Acceptance: `python3 scripts/export-timesheet.py --project <N> --customer`.

## How it works

```
Your repo (docs only: CLAUDE.md accounting rule + issue template)
   │ detected by scaffold init, or injected via GitHub API
devledger skill (scripts/ actions · assets/ templates · references/ deep docs)
   │ gh CLI (GraphQL/REST)
GitHub Projects (data layer: issues + 5 fields)
```

Requires `gh` CLI (project scopes), bash 3.2+, python3+openpyxl for exports. Works with ZCode, Claude Code, Cursor — any agent that reads SKILL.md/AGENTS.md.

## Documentation

- [SKILL.md](SKILL.md) — agent entry point (decision tree + per-scenario commands)
- [references/pitfalls.md](references/pitfalls.md) — 9 hard-won gh/GitHub API pitfalls
- [references/methodology.md](references/methodology.md) — principles, data model, migration patterns

## License

[MIT](LICENSE)

---

# 中文说明


把 AI 开发会话自动转化为 **issue + 工时账本**（GitHub Projects）。符合 [Agent Skills 规范](https://agentskills.io/specification)：`SKILL.md` 为 Agent 执行入口（渐进披露），坑清单与方法论在 `references/`，动作脚本在 `scripts/`，模板在 `assets/`。

## 流程总览

```
新项目：脚手架建仓（名含客户名）→ init-project.sh 自动检测并接入 devledger → push → PM 就绪
日常：  正常开发，AI 会话收尾自动记账三步（issue + 5 字段）
查看：  问 AI「最近干了啥」；验收时一句话出 xlsx
```

## 快速上手

```bash
git clone git@github.com:guanlili/devledger.git ~/.agents/skills/devledger
bash ~/.agents/skills/devledger/scripts/install.sh            # 幂等自检
~/devledger/scripts/new-project.sh <owner/repo> [--local <路径>]  # 建项（Project 名=仓库名）
python3 ~/devledger/scripts/export-timesheet.py --project <N> [--customer]  # 验收表
```

| 路径 | 用途 |
|---|---|
| `SKILL.md` | **Agent 执行入口**：决策树 + 场景命令 |
| `AGENTS.md` | 跨 Agent（Claude Code/Cursor 等）接口与红线 |
| `scripts/new-project.sh` | 一键建项：Project（Status 中文化+5字段+View 8列）+ labels + 规范注入 |
| `scripts/export-timesheet.py` | 验收 xlsx（动态列，甲方版 `--customer`） |
| `scripts/reconcile.py` | 字段对账（读回→diff→补写循环；`--from-labels` 重建） |
| `scripts/install.sh` | 幂等安装自检 |
| `references/pitfalls.md` | 9 条实测坑（执行 API 前必读） |
| `references/methodology.md` | 方法论：原则/数据模型/原生取舍/历史迁移 |
| `references/data/*.json` | 各项目账本真值（reconcile 用） |

## 已接入项目

已在多个交付项目上实战运行（内部私有仓库）；接入你的第一个项目只需一条命令。

## 他人一句话接入

对其 AI 说：「克隆 guanlili/devledger 到 ~/.agents/skills/devledger，跑 install.sh，按 SKILL.md 给我的仓库 <owner/repo> 接入项目管理」。管理员需先：加 devledger 仓库协作者 + 确认目标仓库写权限。
