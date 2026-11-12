#!/usr/bin/env bash
# 通用 GitHub 项目管理一键建项：建 Project + 6 字段 + Status 中文化 + View 1 配列 + 仓库类型 labels
# 用法: new-project.sh <owner/repo>   → Project 名=仓库名（客户名含在仓库名里，零额外输入）
# 例:   new-project.sh yourorg/any-repo        → Project 名 = any-repo
# 兼容 macOS 自带 bash 3.2：无关联数组；变量一律 ${VAR} 花括号；$VAR 不紧跟多字节字符
set -euo pipefail

REPO="${1:-}"
LOCAL_DIR=""
if [ "${2:-}" = "--local" ]; then
  LOCAL_DIR="${3:-$(pwd)}"
fi
if [ -z "${REPO}" ]; then
  echo "用法: new-project.sh <owner/repo> [--local <项目路径>]   Project 名=仓库名（客户名请含在仓库名里）" >&2
  exit 1
fi
REPO_NAME="${REPO##*/}"
TITLE="${REPO_NAME}"
PACE=2   # 写操作间隔秒数，防次级限流

say() { printf '==> %s\n' "$*" >&2; }

gql() { # gql '<query>' [额外gh参数...] → stdout 透传 gh 输出；失败重试，耗尽时打印真实错误
  local q="$1" attempt out errf; shift
  errf=$(mktemp)
  for attempt in 1 2 3 4; do
    if out=$(gh api graphql -f query="${q}" "$@" 2>"${errf}"); then
      printf '%s' "${out}"; rm -f "${errf}"; return 0
    fi
    say "  graphql 失败(第${attempt}次)，重试..."
    sleep $((attempt * 15))
  done
  say "graphql 重试耗尽，最后错误: $(cat "${errf}")"; rm -f "${errf}"; return 1
}

mkfield() { # $1=字段名 $2=类型 $3=选项(可空) → stdout 输出 field id；幂等+重试
  local id out attempt
  # 幂等去重走 gql() 带重试直查：裸 gh project field-list 撞次级限流时 stdout 无 JSON，
  # jq 静默空转会被误判「字段不存在」→ 重复创建被拒 → 脚本崩溃（2026-11-09 实测）。
  # 原则：查询失败≠字段不存在——gql 重试耗尽即中止，绝不落入创建分支。
  id=$(gql "query { viewer { projectV2(number: ${PJ_NUM}) { fields(first: 50) { nodes { ... on ProjectV2FieldCommon { id name } } } } } }" \
       --jq '.data.viewer.projectV2.fields.nodes[]? | select(.name == "'"${1}"'") | .id' | head -1)
  case "${id}" in
    PVT*) echo "${id}"; return 0 ;;  # 已存在，幂等复用
    "")   : ;;                       # 查询成功且确认不存在 → 走创建
    *)    say "字段「${1}」去重拿到非法 id：${id}，中止"; exit 1 ;;
  esac
  for attempt in 1 2 3; do
    if [ -n "${3:-}" ]; then
      out=$(gh project field-create "${PJ_NUM}" --owner "@me" --name "${1}" \
              --data-type "${2}" --single-select-options "${3}" --format json 2>/dev/null)
    else
      out=$(gh project field-create "${PJ_NUM}" --owner "@me" --name "${1}" \
              --data-type "${2}" --format json 2>/dev/null)
    fi
    if [ -n "${out}" ]; then jq -r .id <<<"${out}"; sleep "${PACE}"; return 0; fi
    say "  字段「${1}」创建失败(第${attempt}次)，重试..."
    sleep $((attempt * 10))
  done
  say "字段 ${1} 创建失败"; exit 1
}

# ---------- 1. 建 Project（PM_RESUME=<编号> 可续跑半成品） ----------
if [ -n "${PM_RESUME:-}" ]; then
  PJ_NUM="${PM_RESUME}"
  PJ_JSON=$(gql "query { viewer { projectV2(number: ${PJ_NUM}) { id url title } } }" --jq '.data.viewer.projectV2')
  PJ_ID=$(jq -r .id <<<"${PJ_JSON}")
  PJ_URL=$(jq -r .url <<<"${PJ_JSON}")
  say "续跑 Project #${PJ_NUM}  ${PJ_URL}"
else
  say "创建 Project: ${TITLE}"
  PJ_EXIST=$(gql "query { viewer { projectsV2(first: 30) { nodes { number title url id } } } }" --jq '.data.viewer.projectsV2.nodes' || true)
  PJ_JSON=$(jq -c --arg t "${TITLE}" '.[] | select(.title == $t)' <<<"${PJ_EXIST}" 2>/dev/null | head -1)
  if [ -n "${PJ_JSON:-}" ] && [ "${PJ_JSON}" != "null" ]; then
    PJ_NUM=$(jq -r .number <<<"${PJ_JSON}"); PJ_ID=$(jq -r .id <<<"${PJ_JSON}"); PJ_URL=$(jq -r .url <<<"${PJ_JSON}")
    say "  复用已存在的 Project #${PJ_NUM}（同名去重，重跑安全）"
  else
  PJ_JSON=""
  for attempt in 1 2 3 4; do
    if PJ_JSON=$(gh project create --owner "@me" --title "${TITLE}" --format json 2>/dev/null); then break; fi
    say "  创建失败(第${attempt}次)，重试..."
    sleep $((attempt * 15))
    PJ_JSON=""
  done
  [ -n "${PJ_JSON}" ] || { say "Project 创建失败"; exit 1; }
  PJ_NUM=$(jq -r .number <<<"${PJ_JSON}")
  PJ_ID=$(jq -r .id <<<"${PJ_JSON}")
  PJ_URL=$(jq -r .url <<<"${PJ_JSON}")
  say "  Project #${PJ_NUM}  ${PJ_URL}（中断后可 PM_RESUME=${PJ_NUM} 续跑）"
  sleep "${PACE}"
  fi
fi

# ---------- 2. 建 6 个自定义字段 ----------
FID_FTYPE=$(mkfield  "类型"     SINGLE_SELECT "需求,缺陷,优化,交付线,文档")
say "  字段ok 类型=${FID_FTYPE}"
FID_FHOURS=$(mkfield "工时(h)"  NUMBER        "")
say "  字段ok 工时=${FID_FHOURS}"
FID_FSTART=$(mkfield "开始"     DATE          "")
say "  字段ok 开始=${FID_FSTART}"
FID_FEND=$(mkfield   "结束"     DATE          "")
say "  字段ok 结束=${FID_FEND}"
FID_FSOURCE=$(mkfield "来源"    SINGLE_SELECT "甲方,内部")
say "  字段ok 来源=${FID_FSOURCE}"
FID_FREQ=$(mkfield   "需求人"   TEXT          "")
say "  字段ok 需求人=${FID_FREQ}"

# ---------- 3. Status 选项中文化 ----------
say "Status 选项中文化"
ALL_FIELDS=$(gql "query { node(id: \"${PJ_ID}\") { ... on ProjectV2 { fields(first: 30) { nodes { ... on ProjectV2FieldCommon { id name } } } } } }" \
             --jq '.data.node.fields.nodes')
STATUS_ID=$(jq -r '.[] | select(.name == "Status") | .id' <<<"${ALL_FIELDS}")
TITLE_ID=$(jq -r '.[] | select(.name == "Title") | .id' <<<"${ALL_FIELDS}")
ASSIGNEE_ID=$(jq -r '.[] | select(.name == "Assignees") | .id' <<<"${ALL_FIELDS}")
# 坑6：singleSelectOptions 重交会清空全部条目已选值——选项已一致时必须跳过 mutation（读回比对）
CURRENT_OPTS=$(gql "query { node(id: \"${STATUS_ID}\") { ... on ProjectV2SingleSelectField { options { name } } } }" \
               --jq '[.data.node.options[].name] | join(",")')
if [ "${CURRENT_OPTS}" = "待办,开发中,已完成" ]; then
  say "  Status 选项已是中文，跳过（坑6：重交会清空条目已选值）"
else
  gql "mutation { updateProjectV2Field(input: {fieldId: \"${STATUS_ID}\", singleSelectOptions: [
    {name: \"待办\", color: GRAY, description: \"\"},
    {name: \"开发中\", color: YELLOW, description: \"\"},
    {name: \"已完成\", color: GREEN, description: \"\"}
  ]}) { projectV2Field { ... on ProjectV2SingleSelectField { options { name } } } } }" >/dev/null
  say "  Status=${STATUS_ID} 选项: 待办/开发中/已完成"
  sleep "${PACE}"
fi

# ---------- 4. View 1 配可见列（API 建的字段不会自动进视图） ----------
say "配置 View 1 可见列"
VIEW_ID=$(gql "query { node(id: \"${PJ_ID}\") { ... on ProjectV2 { views(first: 5) { nodes { id name } } } } }" \
          --jq '.data.node.views.nodes[0].id')
VFIDS="\"${TITLE_ID}\", \"${STATUS_ID}\", \"${FID_FTYPE}\", \"${FID_FHOURS}\", \"${FID_FSTART}\", \"${FID_FEND}\", \"${FID_FSOURCE}\", \"${FID_FREQ}\", \"${ASSIGNEE_ID}\""
gql "mutation { updateProjectV2View(input: {viewId: \"${VIEW_ID}\", configuration: {visibleFieldIds: [${VFIDS}]}}) { projectV2View { name } } }" >/dev/null
say "  View 1 已配 9 列"
sleep "${PACE}"

# ---------- 5. 仓库类型 labels ----------
say "仓库 ${REPO} 建 5 个类型 label"
for l in "需求:0E8A16" "缺陷:D93F0B" "优化:1D76DB" "交付线:5319E7" "文档:705721"; do
  gh label create "${l%%:*}" -R "${REPO}" --color "${l##*:}" --force >/dev/null 2>&1 || true
  sleep 1
done

# ---------- 6. 注入规范（--local=本地占位符替换；否则 API 注入） ----------
if [ -n "${LOCAL_DIR}" ]; then
  say "本地模式：替换 ${LOCAL_DIR} 中的 __PM_PROJECT__ 占位符"
  CHANGED=0
  for f in "${LOCAL_DIR}/CLAUDE.md" "${LOCAL_DIR}/AGENTS.md" "${LOCAL_DIR}/.github/ISSUE_TEMPLATE/需求.md"; do
    if [ -f "${f}" ] && grep -q "__PM_PROJECT__" "${f}"; then
      sed -i '' "s/__PM_PROJECT__/${PJ_NUM}/g" "${f}"
      CHANGED=$((CHANGED+1))
      say "  已替换 ${f}"
    fi
  done
  if [ "${CHANGED}" -gt 0 ]; then
    git -C "${LOCAL_DIR}" add CLAUDE.md AGENTS.md .github/ISSUE_TEMPLATE/需求.md 2>/dev/null
    git -C "${LOCAL_DIR}" commit -q -m "chore: devledger 项目管理激活（Project #${PJ_NUM}）" 2>/dev/null
    say "  已本地提交（请自行 push）"
  else
    say "  WARN 未找到占位符（非脚手架项目？改用 API 注入模式重跑不带 --local）"
  fi
else
say "注入记账规范到仓库（CLAUDE.md + AGENTS.md + issue 模板）"
PM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO="${REPO}" PJ_NUM="${PJ_NUM}" PJ_URL="${PJ_URL}" PJ_TITLE="${TITLE}" PM_DIR="${PM_DIR}" python3 - <<'PYEOF'
import base64, json, os, subprocess, sys, urllib.parse

repo, num, url, title, pmdir = (os.environ[k] for k in ("REPO", "PJ_NUM", "PJ_URL", "PJ_TITLE", "PM_DIR"))
section = open(f"{pmdir}/assets/claude-section.template.md", encoding="utf-8").read()
# 占位符双保险：新版 __PM_PROJECT__ 与旧版 {PJ_*} 都替换（坑7教训：注入后 grep 验证）
section = section.replace("__PM_PROJECT__", num).replace("{PJ_TITLE}", title).replace("{PJ_URL}", url).replace("{PJ_NUM}", num)
agents_tpl = open(f"{pmdir}/assets/agents-section.template.md", encoding="utf-8").read().replace("__PM_PROJECT__", num)
issue_tpl = open(f"{pmdir}/assets/issue-template.md", encoding="utf-8").read().replace("__PM_PROJECT__", num).replace("{PJ_NUM}", num)
assert "__PM_PROJECT__" not in section and "__PM_PROJECT__" not in issue_tpl and "__PM_PROJECT__" not in agents_tpl, "占位符未替换干净"

def api(path, method="GET", fields=None):
    cmd = ["gh", "api", path]
    if method != "GET":
        cmd += ["-X", method]
    for k, v in (fields or {}).items():
        cmd += ["-f", f"{k}={v}"]
    import time as _t
    for attempt in range(4):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 or any(f"HTTP {status}" in r.stderr for status in (404, 409, 422)):
            return r.returncode, r.stdout, r.stderr
        _t.sleep(10 * (attempt + 1))  # 网络抖动重试
    return r.returncode, r.stdout, r.stderr

def read_file(path_in_repo):
    enc = urllib.parse.quote(path_in_repo)
    code, out, err = api(f"repos/{repo}/contents/{enc}")
    if code == 0:
        data = json.loads(out)
        return base64.b64decode(data["content"]).decode("utf-8"), data["sha"]
    if "HTTP 404" in err:
        return "", None
    raise SystemExit(f"读取失败 {path_in_repo}: {err.strip()}")


def put_file(path_in_repo, content, message, old, sha):
    if sha and content.strip() == old.strip():
        print(f"  已存在且内容一致，跳过: {path_in_repo}")
        return
    enc = urllib.parse.quote(path_in_repo)
    fields = {"message": message, "content": base64.b64encode(content.encode()).decode()}
    if sha:
        fields["sha"] = sha
    code, _, err = api(f"repos/{repo}/contents/{enc}", "PUT", fields)
    if code != 0:
        raise SystemExit(f"写入失败 {path_in_repo}: {err.strip()}")
    print(f"  已写入: {path_in_repo}")


# 小节幂等合并：标记已注入→替换到下一顶级标题（保留其后内容）；未注入→追加；返回 None=无需写
def merge_section(old, sec, marker):
    idx = old.find(marker)
    tail = ""
    if idx >= 0:
        nxt = old.find("\n## ", idx + len(marker))
        if nxt >= 0:
            tail = old[nxt:].lstrip("\n")
            old = old[:nxt]
        if old[idx:].strip() == sec.strip() and not tail:
            return None
    base = old[:idx].rstrip() if idx >= 0 else old.rstrip()
    return base + ("\n\n" if base else "") + sec + ("\n" + tail if tail else "\n")

# 用同一次读取的内容和 SHA 合并，避免覆盖并发编辑。
marker = "## 项目管理（devledger"
amarker = "## 项目管理记账（devledger"
for path, template, section_marker in (
    ("CLAUDE.md", section, marker),
    ("AGENTS.md", agents_tpl, amarker),
):
    old, sha = read_file(path)
    base = "# AGENTS.md\n" if path == "AGENTS.md" and sha is None else old
    merged = merge_section(base, template, section_marker)
    if merged is None:
        print(f"  {path} 小节已是最新，跳过")
    else:
        put_file(path, merged, f"chore: {path} 记账规范（Project #{num}）", old, sha)

path = ".github/ISSUE_TEMPLATE/需求.md"
old, sha = read_file(path)
put_file(path, issue_tpl, f"chore: 项目管理 issue 模板（Project #{num}）", old, sha)
PYEOF
fi

cat <<EOF

✅ 建项完成（规范已自动注入仓库）
   Project: #${PJ_NUM}  ${PJ_URL}
   规范注入：${LOCAL_DIR:+本地占位符已替换并提交（--local 模式）}${LOCAL_DIR:-API 已写入 CLAUDE.md + AGENTS.md 小节与 issue 模板}
   验收导出: python3 ~/devledger/export-timesheet.py --project ${PJ_NUM}
EOF
