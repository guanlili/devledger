# 坑速查（11 条，全部实测 2026-11）

执行 gh / GitHub API 操作前必读；详细背景见 methodology.md。

1. **编码**：`gh project item-list` 损坏中文自定义字段名首字节（值正常）→ 读数据一律 `gh api graphql` 直查 ProjectV2
2. **设值**：`gh project item-edit` 用 `--field 名 --value 值`（无 --single-select-option 旗标；寻址方式见坑 11）
3. **限流两层**：主限流以响应中的剩余额度和重置时间为准；次级限流可能影响 REST 和 GraphQL，GitHub 不公开所有触发条件。
   - 2026-11-09 回填 18 条 issue 时，约连续写入 40–70 次后遇到限流，期间 GraphQL 查询和写入均报错。
   - 2026-11-12 回填中，约写入 60 次后遇到限流。静默 12 分钟后单次写入成功，随后再连续写入 5 次又遇到限流。同机另一会话也在等待限流恢复。批量写入时尽量串行，避免多个会话同时写 Project。
   - 限流后暂停写入。优先遵守 `Retry-After`；如果没有该头且 `x-ratelimit-remaining` 为 0，等到 `x-ratelimit-reset`；否则至少等一分钟再试。持续遇到次级限流时指数退避，并设置重试上限。续跑前读回当前状态，只补差异。参见 [GitHub GraphQL 限流说明](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api)和 [REST 限流说明](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)。
4. **视图**：API 建的字段不进已有视图 → `updateProjectV2View` 的 `visibleFieldIds` 配列
5. **mutation 参数**：update/delete 类只收 `fieldId`，不收 `projectId`
6. **选项整体替换**：`updateProjectV2Field.singleSelectOptions` 重交会**清空全部条目已选值** → 改选项后必须全量读回对账重设
7. **读回验证**：批量写以 GraphQL 读回为准（item-edit 会静默失败；item-add 有读回延迟）；对账模式=读回→diff→补写→循环到干净（reconcile.py）
8. **bash 3.2（macOS）**：无关联数组；`$VAR` 一律写 `${VAR}` 且不紧跟中文字符
9. **代理**：终端访问 github.com 网页域（OAuth/push）超时 → 配置 `HTTPS_PROXY` 指向本地代理；api.github.com 通常可直连
10. **GraphQL 手写单行查询会丢右括号**：报错 `Expected NAME, actual: (none)` 且列号=查询末尾 = 少一个 `}`（不是服务端故障）→ 一律多行书写并数平括号。（实测更正：`--value` 通吃所有字段类型含 TEXT，`--text`/`--number`/`--date` 是别名——以读回验证为准，勿轻信文档包括本文件）
11. **item-edit 寻址**：新版 gh 禁止 `--id` 与 `--field`（按名）混用，报 `` `--field` cannot be used with `--id` `` → 按名编辑须 `gh project item-edit <编号> --owner @me --url <issue链接> --field 名 --value 值`；`--id` 只配 `--field-id` + `--project-id`（机器模式）。坑 2 的 `--value` 通吃结论在 --url 模式下继续成立（2026-11-12 jilin-flex-platform 8 条回填实测，gh 2.103.3）
