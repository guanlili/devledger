# 坑速查（9 条，全部实测 2026-11）

执行 gh / GitHub API 操作前必读；详细背景见 methodology.md。

1. **编码**：`gh project item-list` 损坏中文自定义字段名首字节（值正常）→ 读数据一律 `gh api graphql` 直查 ProjectV2
2. **设值**：`gh project item-edit` 用 `--field 名 --value 值`（无 --single-select-option 旗标）
3. **限流两层**：主 5000 点/小时（等 `rateLimit.resetAt`）；次级限流=连续写触发（静默 5-10 分钟，间隔数秒低速重试，勿快试加剧）
4. **视图**：API 建的字段不进已有视图 → `updateProjectV2View` 的 `visibleFieldIds` 配列
5. **mutation 参数**：update/delete 类只收 `fieldId`，不收 `projectId`
6. **选项整体替换**：`updateProjectV2Field.singleSelectOptions` 重交会**清空全部条目已选值** → 改选项后必须全量读回对账重设
7. **读回验证**：批量写以 GraphQL 读回为准（item-edit 会静默失败；item-add 有读回延迟）；对账模式=读回→diff→补写→循环到干净（reconcile.py）
8. **bash 3.2（macOS）**：无关联数组；`$VAR` 一律写 `${VAR}` 且不紧跟中文字符
9. **代理**：终端访问 github.com 网页域（OAuth/push）超时 → 前缀 `HTTPS_PROXY=http://127.0.0.1:7897`；api.github.com 可直连
