## 项目管理记账（devledger，硬性纪律）

任何 AI 会话（Codex / Claude Code / Cursor 等）完成一个可交付单元后、结束会话前**必须记账**——不可跳过、不可「下次一起补」，没记账的工作等于没做。主账本：GitHub Project `#__PM_PROJECT__`（工具与方法论：本机 `~/.agents/skills/devledger`）。

记账三步：

1. 当轮 commits 聚类成可交付单元（甲方可感知的主题，一次 commit ≠ 一条）；commit message 末尾带 issue 号 `(#N)` 自动关联
2. 按模板建 issue（`.github/ISSUE_TEMPLATE/需求.md`：来源[含甲方原话]/描述[为什么现在做·否决方案·做了什么]/交付物/验证/工时，label=类型；决策上下文记录时写全，事后不可补）。保存 issue URL，已有 issue 直接复用。
3. 用 `python3 ~/.agents/skills/devledger/scripts/bookkeep.py --project __PM_PROJECT__ --issue <issue URL> --type <类型> --source <来源> --hours <人类等价工时> --start <YYYY-MM-DD> --end <YYYY-MM-DD>` 入板、补字段并读回，确认后关闭 issue。甲方需求加 `--requester <需求人>`。中断后使用相同 URL 和参数续跑。

**issue 是唯一工作真相源**：字段与任何汇总均为派生视图。已知坑与扩展工具见 `~/.agents/skills/devledger/SKILL.md`。
