#!/usr/bin/env bash
# devledger 2 分钟演示：全自动「建沙盒仓库 → 接入 → 记 2 条账 → 导出验收表」
# 无需 AI、无需你的真实仓库，跑完即看懂全流程。用法：bash demo.sh
set -euo pipefail
DL="$(cd "$(dirname "$0")/.." && pwd)"
say() { printf '==> %s\n' "$*" >&2; }

say "[1/5] 创建沙盒仓库（私有）"
NAME="devledger-demo-$(date +%m%d%H%M)"
gh repo create "${NAME}" --private --description "devledger demo sandbox，可随时删除" >/dev/null
LOGIN=$(gh api user --jq .login)
REPO="${LOGIN}/${NAME}"
say "  ${REPO}"

say "[2/5] 一条命令接入（建 Project + 字段 + 视图 + 规范注入）"
ONLOG=$(mktemp)
bash "${DL}/scripts/new-project.sh" "${REPO}" >"${ONLOG}" 2>&1 || { cat "${ONLOG}"; say "接入失败"; exit 1; }
grep -E 'Project #|建项完成' "${ONLOG}" | head -2 || true
rm -f "${ONLOG}"

say "[3/5] 记 2 条账（模拟 AI 会话收尾的产出）"
N=$(gh api graphql -f query='{viewer{projectsV2(first:10){nodes{number title}}}}' \
     --jq ".data.viewer.projectsV2.nodes[] | select(.title == \"${NAME}\") | .number" | head -1)
DEMO1=$(mktemp /tmp/dl-demo1.XXXXXX.md); DEMO2=$(mktemp /tmp/dl-demo2.XXXXXX.md)
cat > "${DEMO1}" <<'MD'
## 来源
甲方（示例：「首页太慢了，客户都在抱怨」）

## 描述
### 为什么现在做
客户明确反馈，影响续约（示例数据）

### 考虑过但没选的方案
服务端渲染改造（改动过大，本次不做）

### 具体做了什么
首屏资源瘦身，去掉未使用依赖

## 交付物
- 提交：`abc1234 perf: 首屏瘦身 (#1)`

## 验证
打包体积 841KB→641KB（gzip），Lighthouse 92→98

## 工时
8h（人类等价工作量，从宽）
MD
cat > "${DEMO2}" <<'MD'
## 来源
内部（上线前压测发现）

## 描述
### 为什么现在做
全年数据首次预测必然超时（300s 上限）

### 考虑过但没选的方案
改异步任务（不动数值但要改交互）

### 具体做了什么
训练窗口加封顶，计算量降 26 倍

## 交付物
- 提交：`def5678 fix: 训练规模封顶 (#2)`

## 验证
全年数据 504→82s 通过；缓存命中 1.5s

## 工时
5h（人类等价工作量，从宽）
MD
for pair in "首页性能优化:优化:甲方:8:${DEMO1}" "预测超时修复:缺陷:内部:5:${DEMO2}"; do
  IFS=':' read -r T TY SRC H BODY <<<"${pair}"
  U=$(gh issue create -R "${REPO}" --title "${T}" --body-file "${BODY}" --label "${TY}" --assignee @me)
  NUM=${U##*/}
  REQUESTER=()
  if [ "${SRC}" = "甲方" ]; then
    REQUESTER=(--requester "示例联系人")
  fi
  python3 "${DL}/scripts/bookkeep.py" --project "${N}" --issue "${U}" \
    --type "${TY}" --source "${SRC}" --hours "${H}" --start 2026-01-10 --end 2026-01-10 \
    ${REQUESTER[@]+"${REQUESTER[@]}"} >/dev/null
  say "  #${NUM} ${T}（${TY}/${SRC}/${H}h）已入账"
done
rm -f "${DEMO1}" "${DEMO2}"

say "[4/5] 一条命令导出验收表"
OUT="${HOME}/devledger-demo-timesheet.xlsx"
python3 "${DL}/scripts/export-timesheet.py" --project "${N}" -o "${OUT}"

say "[5/5] 完成——三处看效果"
cat <<EOF

📊 验收表（Excel 打开看）：${OUT}
🗂  看板（字段/视图一目了然）：https://github.com/users/${LOGIN}/projects/${N}
📦 沙盒仓库（issue 四段正文）：https://github.com/${REPO}

清理演示（看完即可删）：
  gh project delete ${N} --owner "@me"
  网页删除仓库：https://github.com/${REPO}/settings（Danger Zone）

这就是 devledger 的全部：接入一条命令、记账一段 issue、验收一张表。
下一步：对你的真实仓库跑 scripts/new-project.sh <owner/repo>
