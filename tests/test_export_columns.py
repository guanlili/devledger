"""导出动态列行为锁定：轮次全空自动省列、合计行落位工时列。"""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("et", ROOT / "scripts" / "export-timesheet.py")
et = importlib.util.module_from_spec(spec)
spec.loader.exec_module(et)
ORIGINAL_COLUMNS = list(et.COLUMNS)


def make_row(**kw):
    base = {c: "" for c in ORIGINAL_COLUMNS}
    base.update(kw)
    return base


class TestDynamicColumns(unittest.TestCase):
    def test_rounds_dropped_when_all_empty(self):
        wb = et.build_sheet([make_row(需求名称="a", **{"工时(h)": 4})], "T", "s")
        headers = [c.value for c in wb["验收汇总"][5]]
        self.assertNotIn("交付轮次", headers)
        self.assertEqual(headers[0], "需求名称")

    def test_rounds_kept_when_present(self):
        wb = et.build_sheet([make_row(需求名称="a", **{"工时(h)": 4, "交付轮次": "R1"})], "T", "s")
        headers = [c.value for c in wb["验收汇总"][5]]
        self.assertIn("交付轮次", headers)

    def test_total_row_at_hours_column(self):
        rows = [make_row(需求名称="a", **{"工时(h)": 4}), make_row(需求名称="b", **{"工时(h)": 6})]
        wb = et.build_sheet(rows, "T", "s")
        ws = wb["验收汇总"]
        last = [c.value for c in ws[ws.max_row]]
        hours_idx = [c.value for c in ws[5]].index("工时(h)")
        self.assertEqual(last[0], "合计")
        self.assertEqual(last[hours_idx], 10)


class TestExportValidation(unittest.TestCase):
    def test_blank_hours_are_reported_and_zero_is_valid(self):
        rows = [make_row(需求名称="空工时"), make_row(需求名称="零工时", **{"工时(h)": 0})]
        wb = et.build_sheet(rows, "T", "s")
        self.assertEqual(wb["缺失工时"]["A2"].value, "空工时")
        self.assertEqual(wb["缺失工时"].max_row, 2)
        ws = wb["验收汇总"]
        self.assertEqual(ws.cell(row=ws.max_row, column=1).value, "已填工时合计")

    def test_formula_like_text_stays_text(self):
        wb = et.build_sheet([make_row(需求名称="=1+1", 类型="=2+2")], "=3+3", "")
        self.assertEqual(wb["验收汇总"]["A6"].data_type, "s")
        self.assertEqual(wb["验收汇总"]["A6"].value, "=1+1")
        self.assertEqual(wb["验收汇总"]["A1"].data_type, "s")
        self.assertEqual(wb["工时概览"]["B2"].data_type, "s")


if __name__ == "__main__":
    unittest.main()
