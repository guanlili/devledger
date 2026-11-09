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

ITEMS_Q = '''query { viewer { projectV2(number: %d) { items(first: 100) {
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
    data = gql(ITEMS_Q % project)
    if not data:
        sys.exit("读取 Project 失败（限流？稍后重跑）")
    items = []
    for n in data["viewer"]["projectV2"]["items"]["nodes"]:
        c = n.get("content")
        if not c:
            continue
        vals = {}
        for f in n["fieldValues"]["nodes"]:
            fn = (f.get("field") or {}).get("name")
            if fn and fn not in vals:
                vals[fn] = f.get("text") if "text" in f else (f.get("name") or f.get("number") or f.get("date"))
        items.append({"title": c["title"], "url": c["url"], "vals": vals})
    return items


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

    for sweep in range(1, args.sweeps + 1):
        todo = plan_changes(read_items(args.project), args.field, args.value, args.where)
        print(f"[sweep{sweep}] 需修改 {len(todo)} 条", flush=True)
        if not todo:
            print("FILL CLEAN")
            return
        if args.dry_run:
            for it in todo[:15]:
                print(f"  DRIFT {it['title'][:36]} | 现={it['vals'].get(args.field)!r} → {args.value!r}")
            return
        for it in todo:
            rc, _, err = run(["gh", "project", "item-edit", str(args.project), "--owner", "@me",
                              "--url", it["url"], "--field", args.field, "--value", args.value], pace=1.5)
            if rc != 0:
                print(f"  FAIL {it['title'][:30]}: {err[:60]}", flush=True)
        time.sleep(10)
    print("FILL DONE（达最大轮数，如仍有差异请重跑——幂等只补差异）")


if __name__ == "__main__":
    main()
