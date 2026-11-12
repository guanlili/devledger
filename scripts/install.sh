#!/usr/bin/env bash
# devledger 安装 / 更新 / 自检——三合一，同一条命令（幂等，可反复跑）
#   安装：克隆后 bash scripts/install.sh   （或见 README 一键命令）
#   更新：bash ~/.agents/skills/devledger/scripts/install.sh
set -euo pipefail

DEST="${HOME}/.agents/skills/devledger"
SRC="$(cd "$(dirname "$0")/.." && pwd)"
say() { printf '==> %s\n' "$*" >&2; }

# 1) 就位（未在标准位置则克隆；HTTPS 免 SSH key）
if [ "${SRC}" != "${DEST}" ] && [ ! -d "${DEST}/.git" ]; then
  say "克隆 devledger 到 ${DEST}"
  git clone https://github.com/guanlili/devledger.git "${DEST}"
fi
[ -d "${DEST}/.git" ] || { say "未找到 ${DEST}，请先克隆仓库"; exit 1; }

# 兼容软链：历史文档与已注入项目的正文引用 ~/devledger（标准路径为 ~/.agents/skills/devledger）
if [ "${DEST}" != "${HOME}/devledger" ] && [ ! -e "${HOME}/devledger" ]; then
  ln -s "${DEST}" "${HOME}/devledger" 2>/dev/null && say "兼容软链已建：~/devledger → ${DEST}" || true
fi

# 2) 更新（ff-only；无网/本地改动则跳过，不阻塞自检）
say "检查更新"
git -C "${DEST}" pull --ff-only --quiet 2>/dev/null && say "  已是最新" || say "  跳过更新（离线或本地有改动），继续自检"

# 3) 版本
VER=$(awk '/^  version:/{gsub(/"/,""); print $2}' "${DEST}/SKILL.md" 2>/dev/null || true)
say "devledger ${VER:-unknown}"

# 4) 前置自检
command -v gh >/dev/null 2>&1 || { say "缺 gh CLI：brew install gh（https://cli.github.com），装好后重跑本命令"; exit 1; }
say "gh CLI：$(gh --version | head -1)"
for dep in jq python3; do
  command -v "${dep}" >/dev/null 2>&1 || { say "缺少接入依赖：${dep}，安装后重跑"; exit 1; }
done
gh auth status >/dev/null 2>&1 || { say "未登录 GitHub：gh auth login（浏览器确认一次），再重跑"; exit 1; }
SCOPES=$(gh auth status 2>&1 | grep -o "scopes:.*" || true)
case "${SCOPES}" in
  *project*) say "gh 权限就绪" ;;
  *) say "补 project 权限（浏览器确认一次）"; gh auth refresh -h github.com -s project,read:project || true ;;
esac
python3 -c "import openpyxl" >/dev/null 2>&1 && say "openpyxl 就绪" || say "提示：导出验收表需 pip3 install --user openpyxl（记账不受影响）"

cat <<EOF

✅ devledger ${VER:-} 就绪（安装/更新/自检是同一条命令，坏了随时重跑）
   立即看效果：bash ${DEST}/scripts/demo.sh        # 2 分钟全自动演示
   接入仓库：  bash ${DEST}/scripts/new-project.sh <owner/repo>
   网络超时：  配置 HTTPS_PROXY 指向你的本地代理后重试
