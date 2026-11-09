#!/usr/bin/env bash
# devledger 一键安装（幂等）：克隆/更新 skill 到 ~/.agents/skills/devledger + 前置自检
# 用法：bash install.sh   （在已克隆的 devledger 目录内执行，或由 AI 代跑）
set -euo pipefail

DEST="${HOME}/.agents/skills/devledger"
SRC="$(cd "$(dirname "$0")" && pwd)"
say() { printf '==> %s\n' "$*" >&2; }

# 1) 就位：本目录已是目标位置则跳过；否则克隆/更新
if [ "${SRC}" = "${DEST}" ]; then
  say "已在 ${DEST}（skill 就位）"
else
  if [ -d "${DEST}/.git" ]; then
    say "更新已安装的 ${DEST}"
    git -C "${DEST}" pull --ff-only >/dev/null 2>&1 || say "  更新失败（本地有改动？），沿用现有版本"
  else
    say "克隆 devledger 到 ${DEST}"
    git clone "$(git -C "${SRC}" remote get-url origin 2>/dev/null || echo https://github.com/guanlili/devledger.git)" "${DEST}"
  fi
fi

# 2) gh CLI 检查
if ! command -v gh >/dev/null 2>&1; then
  say "缺少 gh CLI。安装：brew install gh（或 https://cli.github.com/），然后重新运行本脚本"
  exit 1
fi
say "gh CLI 就绪：$(gh --version | head -1)"

# 3) 登录与权限检查
if ! gh auth status >/dev/null 2>&1; then
  say "未登录 GitHub。请执行：gh auth login（浏览器确认一次），然后重新运行本脚本"
  exit 1
fi
SCOPES=$(gh auth status 2>&1 | grep -o "scopes:.*" || true)
case "${SCOPES}" in
  *project*) say "gh 权限就绪（${SCOPES#scopes: }）" ;;
  *) say "缺 project 权限，发起授权（浏览器确认一次）：gh auth refresh -h github.com -s project,read:project"
     gh auth refresh -h github.com -s project,read:project || true ;;
esac

# 4) python + openpyxl（扩展工具用；缺了不影响记账）
if python3 -c "import openpyxl" >/dev/null 2>&1; then
  say "python3 + openpyxl 就绪"
else
  say "提示：验收导出需要 openpyxl（pip3 install --user openpyxl）；日常记账不受影响"
fi

cat <<EOF

✅ devledger 安装完成
   下一步（一句话）：让你的 AI 读 ${DEST}/SKILL.md 并执行
   scripts/new-project.sh <owner/repo> [--local <项目路径>]   # Project 名=仓库名
   若克隆/推送超时：前缀 HTTPS_PROXY=http://127.0.0.1:7897（坑9）
   无 guanlili/devledger 访问权会克隆失败：请仓库主人添加协作者
