#!/usr/bin/env python3
"""通用字段对账引擎：读回 → diff → 补写 → 循环验证到干净（坑7：以读回为准）。

用法：
  python3 reconcile.py --project 4 --repo guanlili/xxx --data data/datang-ledger.json           # 对账+修复
  python3 reconcile.py --project 4 --repo guanlili/xxx --data data/datang-ledger.json --dry-run # 只看差异
  python3 reconcile.py --project N --repo guanlili/xxx --from-labels                            # 按「轮次:」label 重建轮次字段（坑6善后）

数据文件 data/*.json：[{"title": "...", "fields": {"字段": "值", ...}}, ...]（各项目账本真值）。
数字字段（如「工时(h)」）写 2 / 2.0 / "2" 均可：引擎读回后统一归一为字符串再比较。
"""
import argparse
import json
import subprocess
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


def norm(v):
    """字段值归一：数字与数字字符串等价，其余按去空白字符串比较。

    读回侧已把 Project 的数字字段归一为 str(int(x))（见 read_project），
    所以真值文件里写 2 / 2.0 / "2" / "2.0" 都应判定为一致，避免全量误报 DRIFT。
    """
    if v is None:
        return None
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, (int, float)):
        f = float(v)
        return str(int(f)) if f.is_integer() else str(f)
    s = str(v).strip()
    try:
        f = float(s)
        return str(int(f)) if f.is_integer() else str(f)
    except ValueError:
        return s


def run(args, retries=6):
    last = ""
    for a in range(retries):
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            r = type("R", (), {"returncode": 1, "stdout": "", "stderr": "timeout"})()
        if r.returncode == 0:
            return r.returncode, r.stdout.strip(), r.stderr.strip()
        last = r.stderr.strip()
        time.sleep(300 if "rate limit" in last.lower() else 20 * (a + 1))
    return 1, "", last


def read_project(number):
    """GraphQL 读回全部条目及字段值：{title: {url, vals}}。"""
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
            if not c:
                continue
            vals = {}
            for v in n["fieldValues"]["nodes"]:
                fn = v.get("field", {}).get("name")
                if fn == "Status":
                    vals["Status"] = v.get("name")
                elif fn in ("类型", "来源", "交付轮次"):
                    vals[fn] = v.get("name")
                elif fn == "工时(h)":
                    num = v.get("number")
                    vals["工时(h)"] = str(int(num)) if num is not None and float(num).is_integer() else (str(num) if num is not None else None)
                elif fn == "开始":
                    vals["开始"] = v.get("date")
                elif fn == "结束":
                    vals["结束"] = v.get("date")
            items[c["title"]] = {"url": c["url"], "vals": vals}
        if not proj["items"]["pageInfo"]["hasNextPage"]:
            return items
        cursor = proj["items"]["pageInfo"]["endCursor"]


def issue_title_number_map(repo):
    rc, out, _ = run(["gh", "issue", "list", "-R", repo, "--state", "all", "--limit", "300",
                      "--json", "number,title", "--jq", '.[] | "\\(.number)\\t\\(.title)"'])
    m = {}
    if rc == 0:
        for line in out.splitlines():
            n, _, t = line.partition("\t")
            m[t] = n
    return m


def expect_from_labels(repo):
    """按「轮次:<名>」label 生成轮次预期（坑6善后用）。"""
    rc, out, _ = run(["gh", "issue", "list", "-R", repo, "--state", "all", "--limit", "300",
                      "--json", "title,labels", "--jq", '.[] | "\\(.title)\\t\\([.labels[].name] | join(","))"'])
    expect = []
    if rc == 0:
        for line in out.splitlines():
            title, _, labels = line.partition("\t")
            rounds = [l[len("轮次:"):] for l in labels.split(",") if l.startswith("轮次:")]
            if rounds:
                expect.append({"title": title, "fields": {"交付轮次": rounds[0]}})
    return expect


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", type=int, required=True, help="GitHub Project 编号")
    ap.add_argument("--repo", required=True, help="issue 所在仓库 owner/name")
    ap.add_argument("--data", help="账本真值 JSON（与 --from-labels 二选一）")
    ap.add_argument("--from-labels", action="store_true", help="按「轮次:」label 重建交付轮次字段")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.from_labels:
        expect = expect_from_labels(args.repo)
        print(f"从 label 推得 {len(expect)} 条轮次预期", flush=True)
    elif args.data:
        expect = json.load(open(args.data))
    else:
        sys.exit("需要 --data 或 --from-labels")
    print(f"预期 {len(expect)} 条，dry_run={args.dry_run}", flush=True)

    for sweep in range(1, 5):
        items = read_project(args.project)
        if items is None:
            print(f"[sweep{sweep}] 读失败，5 分钟后重试", flush=True)
            time.sleep(300)
            continue
        todo = []
        for e in expect:
            cur = items.get(e["title"])
            for f, v in e["fields"].items():
                if cur is None or norm(cur["vals"].get(f)) != norm(v):
                    todo.append((e["title"], cur["url"] if cur else None, f, v))
        print(f"[sweep{sweep}] project {len(items)} 条，需修正 {len(todo)} 处", flush=True)
        if not todo:
            print("RECONCILE CLEAN", flush=True)
            return
        if args.dry_run:
            for t, _, f, v in todo[:20]:
                print(f"  DRIFT {t} {f}={v}")
            return
        tmap = issue_title_number_map(args.repo)
        for title, url, f, v in todo:
            if url is None:
                n = tmap.get(title)
                if not n:
                    print(f"  缺 issue 本体：{title}", flush=True)
                    continue
                url = f"https://github.com/{args.repo}/issues/{n}"
                rc, _, e = run(["gh", "project", "item-add", str(args.project), "--owner", "@me", "--url", url])
                print(f"  +item-add {title} {'ok' if rc == 0 else e[:60]}", flush=True)
                time.sleep(2)
            rc, _, e = run(["gh", "project", "item-edit", str(args.project), "--owner", "@me",
                            "--url", url, "--field", f, "--value", v])
            if rc != 0:
                print(f"  FAIL {title[:30]} {f}={v}: {e[:60]}", flush=True)
            time.sleep(2)
        time.sleep(30)
    print("RECONCILE DONE（达最大扫描次数，如仍有差异请重跑）", flush=True)


if __name__ == "__main__":
    main()
