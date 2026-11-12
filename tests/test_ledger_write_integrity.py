"""写入前的定位、分页和仓库文件并发保护。"""
import pathlib
import runpy
import unittest
from unittest.mock import Mock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
RECONCILE = runpy.run_path(str(SCRIPTS / "reconcile.py"))
FILL = runpy.run_path(str(SCRIPTS / "fill-field.py"))


class TestReconcileTargets(unittest.TestCase):
    def test_explicit_number_disambiguates_titles(self):
        resolve = RECONCILE["resolve_targets"]
        issues = [{"title": "同名", "number": 1}, {"title": "同名", "number": 2}]
        entry = {"title": "同名", "fields": {"工时(h)": 0}}
        with self.assertRaisesRegex(SystemExit, "标题匹配到 2 条"):
            resolve([entry], "a/r", issues)
        self.assertEqual(list(resolve([dict(entry, number=2)], "a/r", issues)),
                         ["https://github.com/a/r/issues/2"])


class TestFillPagination(unittest.TestCase):
    def test_reads_later_page_and_preserves_zero(self):
        read = FILL["read_items"]

        def page(cursor, nodes):
            return {"viewer": {"projectV2": {"items": {
                "pageInfo": {"hasNextPage": cursor is not None, "endCursor": cursor},
                "nodes": nodes,
            }}}}

        node = {"content": {"title": "后一页", "url": "https://github.com/a/r/issues/101"},
                "fieldValues": {"nodes": [{"field": {"name": "工时(h)"}, "number": 0}]}}
        with patch.dict(read.__globals__, {"gql": Mock(
            side_effect=[page("next", []), page(None, [node])],
        )}):
            rows = read(1)
            self.assertEqual(rows[0]["vals"], {"工时(h)": 0})
            self.assertEqual(read.__globals__["gql"].call_args.kwargs["cursor"], "next")


class TestOnboardingWrites(unittest.TestCase):
    def setUp(self):
        source = (SCRIPTS / "new-project.sh").read_text()
        functions = source[source.index("def read_file("):source.index("# 小节幂等合并")]
        self.env = {"repo": "a/r"}
        exec("import base64, json, urllib.parse\n" + functions, self.env)

    def test_failed_read_does_not_become_creation(self):
        self.env["api"] = Mock(return_value=(1, "", "HTTP 503"))
        with self.assertRaisesRegex(SystemExit, "读取失败"):
            self.env["read_file"]("AGENTS.md")
        self.env["api"].assert_called_once()

    def test_conflict_uses_original_sha_and_fails(self):
        api = Mock(return_value=(1, "", "HTTP 409"))
        self.env["api"] = api
        with self.assertRaisesRegex(SystemExit, "写入失败"):
            self.env["put_file"]("AGENTS.md", "new", "message", "old", "original-sha")
        api.assert_called_once()
        self.assertEqual(api.call_args.args[2]["sha"], "original-sha")
