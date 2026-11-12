#!/usr/bin/env python3
"""按已有 issue URL 补齐 Project 字段，读回确认后关闭 issue。"""

import argparse
import json
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation

from _common import norm, run

FIELDS = {
    "kind": ("类型", "SingleSelect", "name"),
    "source": ("来源", "SingleSelect", "name"),
    "requester": ("需求人", "Text", "text"),
    "hours": ("工时(h)", "Number", "number"),
    "start": ("开始", "Date", "date"),
    "end": ("结束", "Date", "date"),
    "status": ("Status", "SingleSelect", "name"),
}

FIELD_SELECTION = "\n".join(
    f'{key}: fieldValueByName(name: {json.dumps(name, ensure_ascii=False)}) '
    f'{{ ... on ProjectV2ItemField{kind}Value {{ {value} }} }}'
    for key, (name, kind, value) in FIELDS.items()
)

QUERY = """
query($project: Int!, $owner: String!, $repo: String!, $number: Int!, $cursor: String) {
  viewer { projectV2(number: $project) { id } }
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      state
      projectItems(first: 30, after: $cursor, includeArchived: true) {
        pageInfo { hasNextPage endCursor }
        nodes {
          project { id }
          isArchived
          FIELD_SELECTION
        }
      }
    }
  }
}
""".replace("FIELD_SELECTION", FIELD_SELECTION)


def gh(args, *, pace=0):
    rc, out, err = run(["gh", *args], retries=1, pace=pace)
    if rc:
        raise RuntimeError(err or out or f"gh 退出码 {rc}")
    return out


def read_state(project, issue):
    owner, repo, number = issue
    args = ["api", "graphql", "-f", f"query={QUERY}", "-F", f"project={project}",
            "-f", f"owner={owner}", "-f", f"repo={repo}", "-F", f"number={number}"]
    cursor_args = []
    while True:
        response = json.loads(gh(args + cursor_args))
        if response.get("errors"):
            raise RuntimeError(str(response["errors"]))
        data = response["data"]
        board = data["viewer"]["projectV2"]
        record = (data.get("repository") or {}).get("issue")
        if not board or not record:
            raise RuntimeError("无法读取目标 Project 或 issue，请检查编号和权限")
        page = record["projectItems"]
        for item in page["nodes"]:
            if item["project"]["id"] != board["id"]:
                continue
            if item["isArchived"]:
                raise RuntimeError("目标 Project 中的条目已归档，请先恢复条目")
            values = {
                key: (item.get(key) or {}).get(value)
                for key, (_, _, value) in FIELDS.items()
            }
            return record["state"], values
        if not page["pageInfo"]["hasNextPage"]:
            return record["state"], None
        cursor_args = ["-f", f'cursor={page["pageInfo"]["endCursor"]}']


def pending_fields(current, expected):
    current = current or {}
    return {
        key: value for key, value in expected.items()
        if (norm(current.get(key)) != norm(value) if key == "hours" else current.get(key) != value)
    }


def complete(project, issue, url, expected):
    board_args = [str(project), "--owner", "@me", "--url", url]
    state, current = read_state(project, issue)
    if current is None:
        gh(["project", "item-add", *board_args], pace=1)
        state, current = read_state(project, issue)
        if current is None:
            raise RuntimeError("暂未读到入板条目，请稍后续跑")

    changes = pending_fields(current, expected)
    for key, value in changes.items():
        name = FIELDS[key][0]
        gh(["project", "item-edit", *board_args, "--field", name, "--value", value], pace=1)

    if changes:
        state, current = read_state(project, issue)
        remaining = pending_fields(current, expected)
        if remaining:
            raise RuntimeError("读回仍有差异：" + "、".join(FIELDS[key][0] for key in remaining))

    if state != "CLOSED":
        gh(["issue", "close", url])
        state, current = read_state(project, issue)
        if state != "CLOSED" or pending_fields(current, expected):
            raise RuntimeError("关闭后的读回结果尚未一致，请稍后续跑")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=int, required=True)
    parser.add_argument("--issue", required=True, help="已有 GitHub issue 的完整 URL")
    parser.add_argument("--type", dest="kind", required=True, choices=["需求", "缺陷", "优化", "交付线", "文档"])
    parser.add_argument("--source", required=True, choices=["甲方", "内部"])
    parser.add_argument("--requester", help="需求人，省略时保留现有值")
    parser.add_argument("--hours", required=True, help="非负的人类等价工时")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()
    match = re.fullmatch(r"https://github\.com/([\w.-]+)/([\w.-]+)/issues/([1-9]\d*)/?", args.issue)
    if not match or args.project < 1:
        parser.error("请提供有效的 GitHub issue URL 和正整数 Project 编号")
    try:
        hours = Decimal(args.hours)
        if not hours.is_finite() or hours < 0:
            raise ValueError
        start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
        if start.isoformat() != args.start or end.isoformat() != args.end or start > end:
            raise ValueError
    except (InvalidOperation, ValueError):
        parser.error("工时必须为非负有限数字，日期须为 YYYY-MM-DD，且开始不晚于结束")
    expected = {key: getattr(args, key) for key in FIELDS if key != "status" and getattr(args, key) is not None}
    expected["status"] = "已完成"
    try:
        complete(args.project, match.groups(), args.issue.rstrip("/"), expected)
    except (RuntimeError, ValueError) as exc:
        sys.exit(f"记账未确认完成：{exc}\n请用同一 issue URL 和参数续跑：{args.issue}")
    print(f"记账完成，已读回确认：{args.issue}")


if __name__ == "__main__":
    main()
