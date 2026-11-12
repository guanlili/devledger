#!/usr/bin/env python3
"""通用字段对账引擎：读回 → diff → 补写 → 循环验证到干净（坑7：以读回为准）。

用法：
  python3 reconcile.py --project 4 --repo guanlili/xxx --data data/datang-ledger.json           # 对账+修复
  python3 reconcile.py --project 4 --repo guanlili/xxx --data data/datang-ledger.json --dry-run # 只看差异
  python3 reconcile.py --project N --repo guanlili/xxx --from-labels                            # 按「轮次:」label 重建轮次字段（坑6善后）

数据文件 data/*.json：[{"number": 123, "title": "...", "fields": {"字段": "值", ...}}, ...]。
number 是 --repo 下的 issue 编号。旧文件省略 number 时，要求仓库内标题唯一。
数字字段（如「工时(h)」）写 2 / 2.0 / "2" 均可：引擎读回后统一归一为字符串再比较。
"""
import argparse
import json
import sys
import time

Q = """query($cursor: String) { viewer { projectV2(number: %d) { items(first: 100, after: $cursor) {
  pageInfo { hasNextPage endCursor }
  nodes { content { ... on Issue { number title url } }
    fieldValues(first: 30) { nodes {
      ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
    } } }
} } } } """


import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _common import norm, run  # noqa: E402  （单点维护限流/归一策略）


def read_project(number):
    """GraphQL 读回全部条目及字段值：{url: vals}。"""
    items, cursor = {}, None
    while True:
        args = ["gh", "api", "graphql", "-f", f"query={Q % number}"]
        if cursor:
            args += ["-f", f"cursor={cursor}"]
        rc, out, err = run(args)
        if rc != 0:
            print(f"读失败：{err[:120]}", flush=True)
            return None
        proj = json.loads(out)["data"]["viewer"]["projectV2"]
        for n in proj["items"]["nodes"]:
            c = n.get("content")
            if not c or not c.get("url"):
                continue
            vals = {}
            for v in n["fieldValues"]["nodes"]:
                fn = (v.get("field") or {}).get("name")
                if fn == "Status":
                    vals["Status"] = v.get("name")
                elif fn in ("类型", "来源", "交付轮次"):
                    vals[fn] = v.get("name")
                elif fn == "工时(h)":
                    num = v.get("number")
                    vals["工时(h)"] = str(int(num)) if num is not None and float(num).is_integer() else (str(num) if num is not None else None)
                elif fn == "需求人":
                    vals["需求人"] = v.get("text")
                elif fn == "开始":
                    vals["开始"] = v.get("date")
                elif fn == "结束":
                    vals["结束"] = v.get("date")
            items[c["url"]] = vals
        if not proj["items"]["pageInfo"]["hasNextPage"]:
            return items
        cursor = proj["items"]["pageInfo"]["endCursor"]


def read_repo_issues(repo):
    rc, out, err = run([
        "gh", "api", f"repos/{repo}/issues?state=all&per_page=100", "--paginate",
        "--jq", ".[] | select(has(\"pull_request\") | not) | {number,title,labels:[.labels[].name]}",
    ])
    if rc != 0:
        sys.exit(f"读取仓库 issue 失败：{err}")
    return [json.loads(line) for line in out.splitlines()]


def expect_from_labels(issues):
    """按「轮次:<名>」label 生成轮次预期（坑6善后用）。"""
    expect = []
    for issue in issues:
        rounds = [label[len("轮次:"):] for label in issue["labels"] if label.startswith("轮次:")]
        if rounds:
            expect.append({"number": issue["number"], "title": issue["title"], "fields": {"交付轮次": rounds[0]}})
    return expect


def resolve_targets(expect, repo, issues):
    by_title = {}
    for issue in issues:
        by_title.setdefault(issue["title"], []).append(issue["number"])
    targets = {}
    for entry in expect:
        title = entry.get("title", "")
        number = entry.get("number")
        if number is None:
            matches = by_title.get(title, [])
            if len(matches) != 1:
                sys.exit(f"标题匹配到 {len(matches)} 条 issue：{title!r}，请在数据文件中指定 number")
            number = matches[0]
        if type(number) is not int or number < 1:
            sys.exit(f"无效 issue 编号：{number!r}")
        url = f"https://github.com/{repo}/issues/{number}".lower()
        if url in targets:
            sys.exit(f"数据文件重复指定 issue #{number}")
        targets[url] = (f"#{number} {title}".rstrip(), entry["fields"])
    return targets


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", type=int, required=True, help="GitHub Project 编号")
    ap.add_argument("--repo", required=True, help="issue 所在仓库 owner/name")
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--data", help="账本真值 JSON（与 --from-labels 二选一）")
    source.add_argument("--from-labels", action="store_true", help="按「轮次:」label 重建交付轮次字段")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.from_labels:
        expect = expect_from_labels(read_repo_issues(args.repo))
        issues = []
    else:
        with open(args.data, encoding="utf-8") as data:
            expect = json.load(data)
        issues = read_repo_issues(args.repo) if any(e.get("number") is None for e in expect) else []
    targets = resolve_targets(expect, args.repo, issues)
    print(f"预期 {len(targets)} 条，dry_run={args.dry_run}", flush=True)

    for sweep in range(1, 6):
        items = read_project(args.project)
        if items is None:
            sys.exit("RECONCILE INCOMPLETE：无法读回 Project")
        current = {url.lower(): vals for url, vals in items.items()}
        todo = []
        for url, (label, fields) in targets.items():
            values = current.get(url)
            changes = {f: v for f, v in fields.items() if values is None or norm(values.get(f)) != norm(v)}
            if changes:
                todo.append((url, label, changes))
        drift = sum(len(changes) for _, _, changes in todo)
        print(f"[sweep{sweep}] project {len(items)} 条，需修正 {drift} 处", flush=True)
        if not todo:
            print("RECONCILE CLEAN", flush=True)
            return
        if args.dry_run:
            for _, label, changes in todo:
                for field, value in changes.items():
                    print(f"  DRIFT {label} {field}={value}")
            return
        if sweep == 5:
            sys.exit(f"RECONCILE INCOMPLETE：读回仍有 {drift} 处差异")
        for url, label, changes in todo:
            if url not in current:
                rc, _, err = run(["gh", "project", "item-add", str(args.project), "--owner", "@me", "--url", url], pace=2)
                if rc != 0:
                    print(f"  FAIL 入板 {label}: {err}", flush=True)
                    continue
            for field, value in changes.items():
                rc, _, err = run(["gh", "project", "item-edit", str(args.project), "--owner", "@me",
                                  "--url", url, "--field", field, "--value", str(value)], pace=2)
                if rc != 0:
                    print(f"  FAIL {label} {field}={value}: {err}", flush=True)
        time.sleep(30)


if __name__ == "__main__":
    main()
