# devledger

[English](README.md) | 简体中文

[![License: MIT](https://img.shields.io/badge/License-MIT-informational)](LICENSE)
[![CI](https://github.com/guanlili/devledger/actions/workflows/ci.yml/badge.svg)](https://github.com/guanlili/devledger/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/guanlili/devledger)](https://github.com/guanlili/devledger/releases)

**研发管理的自动账本。** 没记账的工作等于没做。

devledger 是轻量、符合 [Agent Skills](https://agentskills.io) 规范的 skill：AI 开发会话收尾时，自动把需求、缺陷与工时记进 GitHub Projects 形成账本；验收时一条命令导出交付级汇总表。`SKILL.md` 为 Agent 执行入口（渐进披露），坑清单与方法论在 `references/`，动作脚本在 `scripts/`，模板在 `assets/`。

## 流程总览

**架构**——仓库管文档、skill 管动作、Project 管数据；工具永远不进交付仓库：

```mermaid
graph TB
    subgraph repo["交付仓库（每项目一个）"]
        issue["issue · 唯一真相源"]
        rules["CLAUDE.md / AGENTS.md 记账纪律<br/>+ issue 模板"]
    end
    subgraph skill["devledger skill（本仓库，装一次）"]
        entry["SKILL.md · Agent 决策树"]
        actions["scripts/ · 建项 / 记账 / 对账 / 导出"]
        refs["assets/ 模板 + references/ 方法论与坑"]
    end
    board["GitHub Project 账本<br/>一仓库一 Project · issue + 6 字段"]
    xlsx["验收 xlsx（--customer 甲方版）"]

    actions -- "new-project.sh 注入" --> rules
    actions -- "记账三步（gh CLI）" --> issue
    issue -- "item-add 入板" --> board
    actions -- "reconcile / fill-field 对账" --> board
    actions -- "export-timesheet 导出" --> xlsx
```

**记账三步**——AI 会话收尾的硬性纪律，人零输入：

```mermaid
flowchart LR
    s["AI 开发会话<br/>交付可交付单元"] -->|"① 建 issue"| i["四段正文：来源(含甲方原话)/描述<br/>交付物/验证·工时，label=类型"]
    i -->|"② 入板"| b["Project 看板"]
    b -->|"③ 读回字段后关闭 issue"| f["类型 · 来源 · 需求人<br/>工时(h) · 开始 · 结束"]
    f --> v["看板 / 汇总 = 派生视图"]
    v -. "验收时一条命令" .-> x["交付级 xlsx"]
```

一句话：新项目一条命令接入 → 日常 AI 收尾自动记账 → 验收一句话出表。

## 快速上手

```bash
# ① 2 分钟看效果（自动建沙盒→接入→记 2 条账→导出验收表，无需 AI 和真实仓库）
bash ~/.agents/skills/devledger/scripts/demo.sh
# ② 安装（HTTPS 免 SSH key）
git clone https://github.com/guanlili/devledger.git ~/.agents/skills/devledger
# ③ 接入你的仓库（一条命令）
bash ~/.agents/skills/devledger/scripts/new-project.sh <owner/repo>
```

**更新 = 重跑安装命令**：`bash ~/.agents/skills/devledger/scripts/install.sh`（同一条命令完成 安装/更新/自检，坏了随时重跑）

| 路径 | 用途 |
|---|---|
| `SKILL.md` | **Agent 执行入口**：决策树 + 场景命令 |
| `AGENTS.md` | 跨 Agent（Claude Code/Cursor 等）接口与红线 |
| `scripts/new-project.sh` | 一键建项：Project（Status 中文化+6字段+View 9列）+ labels + 规范注入 |
| `scripts/export-timesheet.py` | 验收 xlsx（动态列，甲方版 `--customer`） |
| `scripts/fill-field.py` | 批量字段填充（读回验证内置，幂等重跑） |
| `scripts/reconcile.py` | 字段对账（读回→diff→补写循环；`--from-labels` 重建） |
| `scripts/install.sh` | 幂等安装自检 |
| `references/pitfalls.md` | 实测避坑指南（执行 API 前必读） |
| `references/methodology.md` | 方法论：原则/数据模型/原生取舍/历史迁移 |
| `references/data/*.json` | 各项目账本真值（reconcile 用） |

## 已接入项目

已在多个交付项目上实战运行（内部私有仓库）；接入你的第一个项目只需一条命令。

**Dogfooding**: devledger's own development is tracked by devledger — [see our live ledger](https://github.com/users/guanlili/projects/13). 本项目自身的开发账本就用 devledger 记（点开即真实数据）。

## 为「一人舰队」（1+N 模式）而生

devledger 面向正在成型的全新协作形态：**一个技术负责人 + 一群 AI Agent**——而不是大团队人间协作（那是 Jira 的问题域，我们永远不解决它）。

```
舰队长（你）                Agent 会话                   devledger
──────────────            ─────────────               ─────────────
判断：做什么/为什么     →   执行：怎么做            →    航海日志：发生过什么
验收：结果对不对            会话收尾必记账               证据 · 工时 · 决策上下文
```

范式四法则（产品宪法）：

1. **判断不委托**——What/Why/验收留在人，How 全部下放
2. **执行必自证**——没记账的会话等于没干活
3. **真相只一份**——issue 是唯一事实源，看板与报表皆派生
4. **工时即度量**——人类等价工时是衡量委托值不值的经济学单位

我们认为 AI 辅助交付的计费与度量是行业空白，devledger 要做它的可运行参考实践——见 [ROADMAP.md](ROADMAP.md)。

## 他人一句话接入

对其 AI 说：「克隆 guanlili/devledger 到 ~/.agents/skills/devledger，跑 install.sh，按 SKILL.md 给我的仓库 <owner/repo> 接入项目管理」。管理员需先：加 devledger 仓库协作者 + 确认目标仓库写权限。

## 支持

- 🐛 报 bug：[提 issue](https://github.com/guanlili/devledger/issues/new?template=bug_report.md)
- 💡 提需求：[feature request](https://github.com/guanlili/devledger/issues/new?template=feature_request.md)
- 💬 使用问答：[GitHub Discussions](https://github.com/guanlili/devledger/discussions)（中英文均可）
- 🔒 安全问题：见 [SECURITY.md](SECURITY.md)
