## 项目管理（devledger，记账硬性规范）

本仓库由人类 + 多个 AI 协作开发，项目管理主账本是 GitHub Project `#13`（devledger skill，工具与方法论在本机 ~/devledger）。

**硬性纪律：任何 AI 会话完成了一个可交付单元（需求/缺陷/修复/交付线/文档），结束会话前必须完成记账三步。不可跳过、不可"下次一起补"——没记账的工作等于没做。**

记账三步：

1. 当轮 commits 聚类成可交付单元（甲方可感知的主题，一次 commit 不等于一条）；commit 末尾尽量带 issue 号 `(#N)` 自动关联
2. 按模板建 issue（`.github/ISSUE_TEMPLATE/需求.md`：来源[含原话]/描述[为什么·否决方案·做了什么]/交付物/验证/工时，label=类型；决策上下文记录时写全，事后不可补）。保存 issue URL，已有 issue 直接复用。
3. 用 `python3 ~/.agents/skills/devledger/scripts/bookkeep.py --project 13 --issue <issue URL> --type <类型> --source <来源> --hours <人类等价工时> --start <YYYY-MM-DD> --end <YYYY-MM-DD>` 入板、补字段并读回，确认后关闭 issue。甲方需求加 `--requester <需求人>`。中断后使用相同 URL 和参数续跑。

**issue 是唯一工作真相源**：字段与任何汇总均为派生视图。已知坑与扩展工具见 ~/devledger/SKILL.md。

