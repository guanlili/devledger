#!/usr/bin/env python3
"""通用批量字段填充：读回 → 比对 → 只改差异 → 复检循环（坑7「以读回为准」内置）。

用法：
  python3 fill-field.py --project 4 --field 需求人 --value 邢静娴                     # 全部条目
  python3 fill-field.py --project 4 --field 需求人 --value 邢静娴 --where 来源=甲方     # 仅来源=甲方
  python3 fill-field.py --project 4 --field 需求人 --value 邢静娴 --dry-run           # 只看将改哪些

说明：--value 通吃字段类型（select/number/date/text 实测均有效）；已正确的条目自动跳过（幂等可重跑）；
限流自动退避，跑不完直接重跑本命令只补差异。
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import gql, norm, run

ITEMS_Q = '''query($cursor: String) { viewer { projectV2(number: %d) { items(first: 100, after: $cursor) {
  pageInfo { hasNextPage endCursor }
  nodes {
    content { ... on Issue { number title url } }
    fieldValues(first: 20) { nodes {
      ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
    } }
  }
} } } }'''


def read_items(project):
    items, cursor = [], None
    while True:
        data = gql(ITEMS_Q % project, cursor=cursor)
        project_data = (data or {}).get("viewer", {}).get("projectV2")
        if not project_data:
            sys.exit("读取 Project 失败，请检查项目编号和访问权限")
        page = project_data["items"]
        for node in page["nodes"]:
            content = node.get("content") or {}
            if not content.get("url"):
                continue
            vals = {}
            for value in node["fieldValues"]["nodes"]:
                field = (value.get("field") or {}).get("name")
                if field and field not in vals:
                    vals[field] = value.get("text", value.get("name", value.get("number", value.get("date"))))
            items.append({"title": content["title"], "url": content["url"], "vals": vals})
        if not page["pageInfo"]["hasNextPage"]:
            return items
        cursor = page["pageInfo"]["endCursor"]


def plan_changes(items, field, value, where=None):
    """返回需要修改的条目（where 过滤 + 与目标值不同的）。纯函数，可单测。"""
    wf, _, wv = (where or "=").partition("=")
    todo = []
    for it in items:
        if where and norm(it["vals"].get(wf)) != norm(wv):
            continue
        if norm(it["vals"].get(field)) == norm(value):
            continue
        todo.append(it)
    return todo


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", type=int, required=True)
    ap.add_argument("--field", required=True)
    ap.add_argument("--value", required=True, help="目标值（通吃类型）")
    ap.add_argument("--where", help="过滤条件，如 来源=甲方（按当前字段值匹配）")
    ap.add_argument("--sweeps", type=int, default=3, help="复检轮数（默认 3）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.sweeps < 1:
        ap.error("--sweeps 必须大于 0")

    for sweep in range(1, args.sweeps + 2):
        todo = plan_changes(read_items(args.project), args.field, args.value, args.where)
        print(f"[sweep{sweep}] 需修改 {len(todo)} 条", flush=True)
        if not todo:
            print("FILL CLEAN")
            return
        if args.dry_run:
            for it in todo[:15]:
                print(f"  DRIFT {it['title'][:36]} | 现={it['vals'].get(args.field)!r} → {args.value!r}")
            return
        if sweep > args.sweeps:
            sys.exit(f"FILL INCOMPLETE：读回仍有 {len(todo)} 条差异")
        for it in todo:
            rc, _, err = run(["gh", "project", "item-edit", str(args.project), "--owner", "@me",
                              "--url", it["url"], "--field", args.field, "--value", args.value], retries=1, pace=1.5)
            if rc != 0:
                sys.exit(f"写入未确认 {it['title']}: {err}。请稍后重跑，脚本将读回再补差异。")
        time.sleep(10)


if __name__ == "__main__":
    main()
