# 通用 GitHub 项目管理方法论（devledger：Project + AI 记账）

> **当前模式（2026-11-06 定）：轻量日常记录**——记账三步 + 5 字段（无交付轮次）。下文涉及轮次/验收/汇总的章节为**扩展能力（默认不启用）**，保留作背景与未来升级参考。

> 2025-11 起在多个真实交付项目上迭代沉淀（首个项目跑通全链路），适用于任何 GitHub 托管的研发项目。
> 定位：**用户只提需求和验收，AI 全程记账，最终交付项目管理表（xlsx）+ 软件部署包。**

## 一、核心原则

1. **账本 = GitHub Project（一个交付线/合同一个 Project）**
   **Project 名=仓库名**，客户名由用户含在仓库名里（如 `acme-order-api`），零额外输入。验收边界 = 合同边界 = 数据边界；跨项目汇总靠导出工具聚合，不靠合并账本。
2. **一条 issue = 一个可交付单元**
   甲方可感知的需求/缺陷/修复主题。一次 commit ≠ 一条；N 个 commits 按主题聚类成一条。
3. **AI-native：每一步都是命令，没有一步需要人点鼠标**
   所有工具非交互、幂等、可断点重跑；规范长在文件里（本目录 + 各仓库 CLAUDE.md），任何 AI 无对话上下文也能接手。
4. **工具与交付仓库分离**
   交付仓库只放文档与 issue 模板；PM 工具统一住 devledger skill（`~/devledger/`）。
5. **每个字段必须被消费**（导出列/流转机制/汇总透视），零摆设字段。反例：优先级（单人+AI 无排期竞争，已删）。
6. **用户无感知（少输入→零输入）**：用户只说业务语言（「新项目 X 开发了」「验收了」「最近干了啥」），一切命令/参数/API 都是 AI 的实现细节。能从上下文推导的绝不问用户（Project 名=仓库名、客户名在仓库名里、轮次名=AI 从工作主题推断）。

## 二、数据模型（7 字段，全项目统一）

| 字段 | 类型 | 取值 | 消费方 |
|---|---|---|---|
| Status | 单选 | 待办 / 开发中 / 已完成 | 看板流转（注意键名是英文） |
| 类型 | 单选 | 需求 / 缺陷 / 优化 / 交付线 / 文档 | 导出分类列、按类型透视；同步打同名 label |
| 工时(h) | 数字 | — | 验收核心列 |
| 开始 / 结束 | 日期 | — | 验收起止列（历史跨度只有显式日期可表达） |
| 来源 | 单选 | 甲方 / 内部 | `--customer` 干净版导出、「响应甲方 N 条」 |
| 交付轮次 | 单选 | 选项 = 轮次名（如「R2 交付 20260901」） | 按轮次导出/汇总的分组键 |

配套：issue 正文四段（来源/描述/交付物/工时，模板见各仓库 `.github/ISSUE_TEMPLATE/`）；缺陷并入同一 Project 用「类型=缺陷」区分，不建独立 Bug 表。

## 三、新项目接入 SOP（一次性，一条命令全自动）

```bash
~/devledger/new-project.sh <owner/repo>
```

自动完成全部六步：建 Project → 建 6 字段 → Status 选项中文化 → View 1 配 9 列 → 仓库建 5 个类型 label → **往仓库写入 CLAUDE.md「记账硬性规范」小节 + `.github/ISSUE_TEMPLATE/需求.md`**（GitHub API 直接提交，免本地克隆）。幂等可重跑，中断后 `PM_RESUME=<编号>` 续跑。

> 规范落地的关键设计：**执行点在每个仓库的 CLAUDE.md**（AI 会话必读入口，含"没记账等于没做"硬性纪律），**保证点在 new-project.sh 自动注入**——建项即规范到位，不依赖人记得去贴文档。2026-11-05 已在一次性测试仓库全链路实测（建项→注入→验证→清理）。

交付轮次选项默认占位「首个交付轮次」，开轮次前改成实际轮次名（网页或 AI）。

## 四、日常运转：AI 每轮收尾记账（五步）

1. 当轮 commits 聚类成可交付单元
2. 按模板建 issue（四段正文）→ 关闭 → `gh project item-add <N> --owner "@me" --url <issue url>`
3. 设 7 字段（`gh project item-edit <N> --owner "@me" --url <url> --field <字段> --value <值>`）
4. 工时统一 AI 评估口径：**人类等价工作量**（熟练工程师完成同样工作所需时长，非 AI 墙钟——2026-11-08 定案，与历史账/飞书记录同口径，AI 压缩的是墙钟不是交付价值），**实时与回填一律从宽、宁多勿漏**（回填仅见 git 结果，过程中的诊断/实测/死胡同不可见，只能量级基准上界），依据写进 issue 工时段；开发期 commit message 末尾带 issue 号 `(#N)`
5. 该仓库 README「交付轮次工时汇总」追加本轮汇总表
6. 新轮次首条 issue 前追加轮次选项并立即 reconcile 重建（见坑 6）；轮次以 `轮次:<名>` label 镜像在 issue 上
7. AI 自动职责（用户无输入）：记账完成后顺手 `reconcile.py --dry-run` 自检有漂移即修；**交付轮次收官时自动导出该轮验收表**并告知位置

## 五、验收导出

```bash
python3 ~/devledger/export-timesheet.py --project <N> [--round 轮次名] [--customer] [-o 路径.xlsx]
```

产出交付级 xlsx：标题块 + 合计行 + 按类型/来源/轮次透视 + issue 超链接。`--customer` 出甲方干净版。

## 六、已知坑（gh/GitHub API，2026-11-05 实测）

1. `gh project item-list` 中文自定义字段名首字符编码损坏（值正常）→ 读数据必须 `gh api graphql` 直查 ProjectV2（export-timesheet.py 即此实现）
2. `gh project item-edit` 设值用 `--field 字段名 --value 值`（此 gh 版本无 `--single-select-option`）
3. 限流两层：主限流 5000 点/小时；**次级限流**——连续几十个写操作即使主配额充足也报 "rate limit already exceeded"，需静默 5-10 分钟低速重试。批量回填分批 + 查 `rateLimit.resetAt`
4. API/CLI 新建字段**不进已有视图** → 必须 `updateProjectV2View` 的 `visibleFieldIds` 配列（new-project.sh 已内置）
5. GraphQL mutation 参数从简：update/delete 类只收 `fieldId`，不收 `projectId`
6. `updateProjectV2Field.singleSelectOptions` 是整体替换，会**清空全部条目的已选值**——补选项后必须全量读回对账重设
7. 批量写以**读回验证**为准（item-edit 会静默失败、item-add 有读回延迟），对账脚本模式：读回→diff→补写→循环到干净

## 七、原生能力取舍记录（2026-11-06 验证）

零输入原则下逐一实测 GitHub 原生能力后的取舍：

- ✅ **采用**：issue 模板机制（.github/ISSUE_TEMPLATE）、commit `(#N)` 自动关联、Insights 图表（日常进度视图）
- ❌ **不采用**（均需网页/secret 人工操作，违反零输入）：Project 模板实例化（**API 无 templateId**——CreateProjectV2Input 仅 ownerId/title/repositoryId/teamId，内省确认；模板只能网页用）、actions/add-to-project（逐仓库配 PAT secret）、closed→Status 内置 workflow（逐面板网页配置，AI 设 Status 本就零成本）、Iteration 字段（API 不能建字段/加周期，每轮需网页点击；single-select + reconcile 自动流更符合零输入）
- 结论：GitHub 原生自动化面向「人在网页」设计；API 全自动路径上，**devledger 脚本建项即最佳实践**，不是重复造轮子而是补位

## 八、脚手架整合（lili-full-stack）

新项目出生即带 PM 占位资产（`__PM_PROJECT__`），`scripts/init-project.sh` 检测到本机 `~/devledger/new-project.sh` 时自动串联 `--local` 激活（零输入）；非脚手架存量仓库走 API 注入模式。

## 九、历史沿革

- 2026-10 前：飞书多维表格手工记账（已冻结为历史，见各项目记忆）
- 2026-11：首个交付项目完成全链路试点（建项/回填/对账/导出），沉淀本方法论
