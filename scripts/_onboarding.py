"""读取仓库已登记的 Project 编号，或激活本地模板。"""

import base64
import re
import subprocess
import sys
from pathlib import Path

DOCS = ("CLAUDE.md", "AGENTS.md")
TEMPLATE = ".github/ISSUE_TEMPLATE/需求.md"
SECTION = re.compile(r"^## 项目管理(?:记账)?（devledger[^\n]*\n(.*?)(?=^## |\Z)", re.M | re.S)
PROJECT = re.compile(r"GitHub Project\s*`?#(\d+)")


def remote_doc(repo, path):
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{path}", "--jq", ".content"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return base64.b64decode(result.stdout).decode("utf-8")
    if "HTTP 404" in result.stderr:
        return ""
    raise SystemExit(f"无法读取 {path}：{result.stderr.strip()}")


def recorded_project(repo, directory):
    numbers = set()
    for name in DOCS:
        if directory:
            path = Path(directory, name)
            content = path.read_text(encoding="utf-8") if path.is_file() else ""
        else:
            content = remote_doc(repo, name)
        for section in SECTION.findall(content):
            numbers.update(PROJECT.findall(section))
    if len(numbers) > 1:
        raise SystemExit("仓库规范登记了多个 Project 编号，请先核对")
    return next(iter(numbers), "")


def activate(directory, project):
    changed = []
    for name in (*DOCS, TEMPLATE):
        path = Path(directory, name)
        if not path.is_file():
            continue
        original = path.read_bytes()
        updated = original.replace(b"__PM_PROJECT__", project.encode("ascii"))
        if updated != original:
            path.write_bytes(updated)
            changed.append(name)
    if changed:
        git = ["git", "-C", directory]
        subprocess.run([*git, "add", "--", *changed], check=True)
        subprocess.run(
            [*git, "commit", "--only", "-m", f"chore: devledger 项目管理激活（Project #{project}）",
             "--", *changed], check=True,
        )
    return len(changed)


if __name__ == "__main__":
    action, first, second = sys.argv[1:]
    if action == "lookup":
        print(recorded_project(first, second))
    else:
        changed = activate(first, second)
        if not changed:
            print("本地规范无需替换。")
