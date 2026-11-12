---
name: devledger
description: 轻量级 GitHub 项目管理 skill——把 AI 开发会话自动转化为 issue 与工时账本（GitHub Projects）。当用户要给仓库建立项目管理、开发收尾记录需求/缺陷与工时、导出验收汇总表、或对账 Project 字段时使用；触发词：项目管理、记账、工时、验收表、建项、new-project、reconcile。
license: MIT
compatibility: 需 gh CLI（scopes 含 project, read:project）、git、bash 3.2+；导出需 python3 + openpyxl；macOS/Linux。
metadata:
  version: "1.4.0"
  author: guanlili
  homepage: https://github.com/guanlili/devledger
---

# devledger：轻量 GitHub 项目管理

角色一句话：**仓库管文档、skill 管动作、Project 管数据**；工具永远不进交付仓库。

## 架构

```
交付仓库（仅文档：CLAUDE.md 记账小节 + .github/ISSUE_TEMPLATE/，含 __PM_PROJECT__ 占位符）
   │ init-project.sh 检测到本 skill 自动串联，或 new-project.sh API 注入
devledger skill（本目录：scripts/ 动作，assets/ 模板，references/ 深度资料）
   │ gh CLI（GraphQL/REST）
GitHub Projects（数据层：issue + 6 字段；一仓库一 Project，名=仓库名）
```

## 使用决策树（Agent 先读这里）

```
用户意图？
├─ 给仓库建项目管理 / 新项目开始开发 → 场景 A（建项，每仓库一次）
├─ 开发会话结束且交付了工作          → 场景 B（记账三步，硬性纪律）
├─ 看进度 / 最近干了啥               → 场景 C1
└─ 导出验收表                        → 场景 C2（休眠扩展）
```

**前置检查**：读目标仓库 CLAUDE.md「项目管理（devledger」小节——真实编号=已接入；`__PM_PROJECT__`=脚手架项目先走场景 A（--local）；无小节=存量仓库走场景 A（API 注入）。

## 场景 A：新仓库接入（每仓库一次）

```bash
scripts/new-project.sh <owner/repo> [--local <项目本地路径>]
# 脚手架项目（本地已克隆）加 --local：替换占位符并本地提交；存量仓库走 API 注入
# 中断续跑：PM_RESUME=<Project编号> 前缀重跑
```

自动完成：Project（名=仓库名，Status 中文化+6字段+View 9列）+ 5 类型 label + 规范注入（CLAUDE.md 小节、AGENTS.md 小节、issue 模板）。验证：`gh project view <编号>` 有 6 个自定义字段。

## 场景 B：日常记账（AI 会话收尾，硬性纪律）

> **没记账的工作等于没做。完成可交付单元的会话，结束前必须完成三步。**

```bash
# ① 按模板写正文，复用已有 issue 或创建一次，保存 URL。
URL=$(gh issue create -R <owner/repo> --title "<可交付单元>" --body-file <正文.md> --label 需求 --assignee @me)
# ② 入板并补齐字段。③ 读回确认后关闭 issue。
python3 scripts/bookkeep.py --project <Project编号> --issue "${URL}" \
  --type 需求 --source 甲方 --requester 张三 --hours 8 --start YYYY-MM-DD --end YYYY-MM-DD
```

- 用同一个 issue URL 和相同参数续跑。命令只补差异，已关闭的 issue 也可补齐字段。内部需求可省略 `--requester`。
- 工时口径：**人类等价工作量、从宽宁多勿漏**，依据写进 issue；commit 末尾带 `(#N)` 自动关联
- **issue 是唯一真相源**：字段与任何汇总均为派生视图

## 场景 C：查看与导出（休眠扩展）

```bash
python3 scripts/reconcile.py --project <N> --repo <owner/repo> --data <账本.json> --dry-run  # C1 对账体检
# 启用交付轮次的仓库可用 --from-labels 替代 --data，仅核对轮次字段
python3 scripts/export-timesheet.py --project <N> [--round 轮次] [--customer] [-o xlsx]  # C2 验收表
python3 scripts/fill-field.py --project <N> --field <字段> --value <值> [--where 来源=甲方] [--dry-run]  # C3 批量填字段（读回验证内置，幂等重跑）
```

## 执行前必读

- **[references/pitfalls.md](references/pitfalls.md)——实测避坑指南**（编码/限流/字段 API 行为/bash 兼容），执行任何 gh API 操作前先读
- 深度背景：[references/methodology.md](references/methodology.md)（原则/数据模型/原生取舍/历史迁移模式）
- 各项目账本真值：本地 `~/devledger-private/data/*.json`（含客户信息不入库；仓库内 example-ledger.json 为格式示例）

## 安装与他人一句话接入

```bash
git clone git@github.com:guanlili/devledger.git ~/.agents/skills/devledger
bash ~/.agents/skills/devledger/scripts/install.sh   # 幂等自检：就位/gh/权限/openpyxl
```

**批量接入多个仓库**：逐仓库跑 `new-project.sh <owner/repo>`（每仓库一次）；已接入仓库重跑安全（幂等，仅补差异）。

**安装/更新/自检同一条命令**（幂等）：`bash ~/.agents/skills/devledger/scripts/install.sh`——未就位则 HTTPS 克隆；重跑即更新（ff pull + 版本显示 + gh 权限自检）。

**小白演示**：`bash scripts/demo.sh`——2 分钟全自动「建沙盒仓库→接入→记 2 条账→导出验收表」，无需 AI 与真实仓库。

他人接入一句话（对其 AI 说）：「克隆 guanlili/devledger 到 ~/.agents/skills/devledger，跑 install.sh，按 SKILL.md 给我的仓库 <owner/repo> 接入项目管理」。Project 建在执行者账号（@me）；克隆 403=需管理员加 devledger 仓库协作者。
