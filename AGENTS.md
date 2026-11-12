# AGENTS.md — devledger skill 给各类 AI Agent 的接口说明

本仓库是 **devledger**：轻量 GitHub 项目管理（日常自动记账）。ZCode 用户经 `~/.agents/skills/devledger/SKILL.md` 自动加载；其他 Agent（Claude Code / Cursor 等）克隆本仓库后，**以 [SKILL.md](SKILL.md) 为唯一执行入口**——其中含架构图、使用决策树与逐场景精确命令。

## 快速判断我该做什么

| 情境 | 动作 | 命令入口 |
|---|---|---|
| 仓库 CLAUDE.md 有「项目管理（devledger」小节+真实编号 | 已接入 → 会话收尾执行**记账三步** | SKILL.md 场景 B |
| 小节含 `__PM_PROJECT__` 占位符（脚手架新项目） | 先**建项**（--local 模式） | SKILL.md 场景 A |
| 无小节（存量仓库要接入） | **建项**（API 注入模式） | SKILL.md 场景 A |
| 用户要看进度/导出验收表 | 唤醒休眠扩展 | SKILL.md 场景 C |

## 红线（违反即错）

1. 工具不进交付仓库——只写文档（CLAUDE.md 小节 / issue 模板），不复制脚本
2. 记账以 **issue 为唯一真相源**，Project 字段只是视图
3. 完成可交付单元的会话**不记账不结束**（硬性纪律）
4. 读 Project 数据一律 `gh api graphql`（`gh project item-list` 会损坏中文字段名）
5. 逐条命令见 SKILL.md 链接的实测避坑指南

## 他人接入（一句话协议）

用户说「克隆 guanlili/devledger 并给我的仓库 X 接入」时：clone → `bash scripts/install.sh`（自检，按提示补 gh 登录/权限）→ 读 SKILL.md 场景 A 执行。Project 建在执行者账号（@me）；克隆 403 = 找管理员加 devledger 仓库协作者。

## 元信息

- 数据层：GitHub Projects（用户级，一仓库一 Project，Project 名=仓库名）
- 字段模型：Status（键名英文）/ 类型 / 来源 / 工时(h) / 开始 / 结束
- 安装位：`~/.agents/skills/devledger`（ZCode）或任意路径（其他 Agent 读文件即可）
