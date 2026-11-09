#!/usr/bin/env python3
"""验收汇总导出：从 GitHub Project 拉取条目生成交付级 xlsx（通用，任意项目）。

用法：
  python3 ~/devledger/scripts/export-timesheet.py                                # 全部条目（--project 必填）
  python3 ~/devledger/scripts/export-timesheet.py --round <轮次名>     # 按交付轮次
  python3 ~/devledger/scripts/export-timesheet.py --customer                     # 只导「来源=甲方」
  python3 ~/devledger/scripts/export-timesheet.py -o 交付/验收汇总.xlsx

说明：数据经 gh api graphql 直查 ProjectV2（gh project item-list 会损坏
中文自定义字段名的编码，勿用）。依赖：gh 已登录、系统 python3 + openpyxl。
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import date

QUERY = """
query($cursor: String) {
  viewer {
    projectV2(number: %d) {
      title
      items(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          content {
            ... on Issue { number title url state }
          }
          fieldValues(first: 30) {
            nodes {
              ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
            }
          }
        }
      }
    }
  }
}
""" 

COLUMNS = ["需求名称", "类型", "来源", "状态", "工时(h)", "开始", "结束", "交付轮次", "链接"]


def gh_graphql(query, cursor=None, retries=3):
    """带重试的 graphql 调用（应对网络抖动）。"""
    args = ["gh", "api", "graphql", "-f", "query=" + query.strip()]
    if cursor:
        args += ["-f", f"cursor={cursor}"]
    last_err = ""
    for attempt in range(retries):
        proc = subprocess.run(args, capture_output=True, text=True)
        if proc.returncode == 0:
            return json.loads(proc.stdout)["data"]["viewer"]["projectV2"]
        last_err = proc.stderr.strip()
        time.sleep(10 * (attempt + 1))
    sys.exit(f"gh api graphql 失败（重试{retries}次）：{last_err}")


def fetch_items(project_number):
    items, cursor = [], None
    while True:
        project = gh_graphql(QUERY % project_number, cursor)
        page = project["items"]
        for node in page["nodes"]:
            content = node.get("content") or {}
            row = {name: "" for name in COLUMNS}
            row["需求名称"] = content.get("title", "")
            row["链接"] = content.get("url", "")
            row["状态"] = "已完成" if content.get("state") == "CLOSED" else "进行中"
            for value in (node.get("fieldValues") or {}).get("nodes", []):
                field = value.get("field", {}).get("name")
                if field == "Status":
                    row["状态"] = value.get("name", row["状态"])
                elif field in row:
                    row[field] = value.get("number", value.get("date", value.get("name", value.get("text", ""))))
            items.append(row)
        if not page["pageInfo"]["hasNextPage"]:
            return project["title"], items
        cursor = page["pageInfo"]["endCursor"]


def build_sheet(rows, project_title, subtitle):
    global COLUMNS
    if rows and all(not r.get("交付轮次") for r in rows):
        COLUMNS = [c for c in COLUMNS if c != "交付轮次"]
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "验收汇总"
    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(bold=True, color="FFFFFF")
    # 交付级表头块：项目名 / 筛选说明 / 导出日期
    ws["A1"] = project_title
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = subtitle
    ws["A3"] = f"导出日期：{date.today():%Y-%m-%d}　制表：GitHub Project 自动生成"
    ws["A3"].font = Font(color="808080")
    ws.append([])
    ws.append(COLUMNS)
    header_row = ws.max_row
    for cell in ws[header_row]:
        cell.fill, cell.font = header_fill, header_font
        cell.alignment = Alignment(horizontal="center")
    rows.sort(key=lambda r: (str(r["开始"]), str(r["需求名称"])))
    for row in rows:
        ws.append([row[c] for c in COLUMNS])
    total = sum(r["工时(h)"] or 0 for r in rows if isinstance(r["工时(h)"], (int, float)))
    hours_col = COLUMNS.index("工时(h)") + 1
    link_col = COLUMNS.index("链接") + 1
    ws.append(["合计" if i == 1 else (total if i == hours_col else "") for i in range(1, len(COLUMNS) + 1)])
    ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
    ws.cell(row=ws.max_row, column=hours_col).font = Font(bold=True)
    widths = {"需求名称": 38, "类型": 8, "来源": 7, "状态": 9, "工时(h)": 9,
              "开始": 12, "结束": 12, "交付轮次": 18, "链接": 44}
    for i, name in enumerate(COLUMNS, 1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(name, 12)
    for r in range(header_row + 1, ws.max_row + 1):
        ws.cell(row=r, column=link_col).hyperlink = ws.cell(row=r, column=link_col).value
    ws.freeze_panes = f"A{header_row + 1}"

    overview = wb.create_sheet("工时概览")
    overview.append(["维度", "取值", "工时(h)", "条数"])
    for cell in overview[1]:
        cell.fill, cell.font = header_fill, header_font
    for dim in ("类型", "来源", "交付轮次"):
        agg = {}
        for r in rows:
            key = str(r[dim] or "未填")
            hours, count = agg.get(key, (0, 0))
            agg[key] = (hours + (r["工时(h)"] if isinstance(r["工时(h)"], (int, float)) else 0), count + 1)
        for key, (hours, count) in sorted(agg.items()):
            overview.append([dim, key, hours, count])
    for i, w in enumerate([10, 24, 10, 8], 1):
        overview.column_dimensions[get_column_letter(i)].width = w
    return wb


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=int, required=True, help="GitHub Project 编号")
    parser.add_argument("--round", help="只导指定交付轮次")
    parser.add_argument("--customer", action="store_true", help='只导「来源=甲方」的条目')
    parser.add_argument("-o", "--output", default=f"验收汇总-{date.today():%Y%m%d}.xlsx")
    args = parser.parse_args()

    project_title, items = fetch_items(args.project)
    if args.round:
        items = [i for i in items if str(i["交付轮次"]) == args.round]
    if args.customer:
        items = [i for i in items if i["来源"] == "甲方"]

    subtitle_parts = []
    if args.round:
        subtitle_parts.append(f"交付轮次：{args.round}")
    subtitle_parts.append("来源：甲方" if args.customer else "来源：全部")
    wb = build_sheet(items, project_title, "　|　".join(subtitle_parts))
    wb.save(args.output)
    hours = sum(i["工时(h)"] for i in items if isinstance(i["工时(h)"], (int, float)))
    customer_count = sum(1 for i in items if i["来源"] == "甲方")
    print(f"已导出 {args.output}：{len(items)} 条，合计 {hours}h，其中甲方来源 {customer_count} 条")


if __name__ == "__main__":
    main()
