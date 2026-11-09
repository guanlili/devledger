"""fill-field 纯逻辑单测：plan_changes 的过滤与幂等跳过。"""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fill_field", ROOT / "scripts" / "fill-field.py")
ff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ff)

ITEMS = [
    {"title": "a", "url": "u1", "vals": {"来源": "甲方", "需求人": "邢静娴"}},
    {"title": "b", "url": "u2", "vals": {"来源": "甲方", "需求人": ""}},
    {"title": "c", "url": "u3", "vals": {"来源": "内部", "需求人": ""}},
]


class TestPlanChanges(unittest.TestCase):
    def test_skip_already_correct(self):
        todo = ff.plan_changes(ITEMS, "需求人", "邢静娴")
        self.assertEqual([i["title"] for i in todo], ["b", "c"])

    def test_where_filter(self):
        todo = ff.plan_changes(ITEMS, "需求人", "邢静娴", where="来源=甲方")
        self.assertEqual([i["title"] for i in todo], ["b"])

    def test_where_numeric_norm(self):
        items = [{"title": "x", "url": "u", "vals": {"工时(h)": 8}}]
        self.assertEqual(ff.plan_changes(items, "工时(h)", 8), [])  # 8 == 8.0 归一后相等
        self.assertEqual(len(ff.plan_changes(items, "工时(h)", "9")), 1)


if __name__ == "__main__":
    unittest.main()
