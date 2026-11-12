"""用模拟 Project 验证中断续跑、关闭顺序和重复执行。"""
import pathlib
import runpy
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
complete = runpy.run_path(str(ROOT / "scripts" / "bookkeep.py"))["complete"]
ISSUE = ("a", "r", "1")
URL = "https://github.com/a/r/issues/1"
EXPECTED = {"hours": "0", "status": "已完成"}


class TestComplete(unittest.TestCase):
    def setUp(self):
        self.write = Mock()
        self.read = Mock()
        mocks = patch.dict(complete.__globals__, {"gh": self.write, "read_state": self.read})
        mocks.start()
        self.addCleanup(mocks.stop)

    def test_resume_writes_only_missing_field_then_closes(self):
        fields = {"hours": 0.0, "status": "已完成"}
        self.read.side_effect = [
            ("OPEN", {"hours": 0.0}),
            ("OPEN", fields),
            ("CLOSED", fields),
        ]
        complete(13, ISSUE, URL, EXPECTED)
        commands = [call.args[0] for call in self.write.call_args_list]
        self.assertEqual(commands[0][-4:], ["--field", "Status", "--value", "已完成"])
        self.assertEqual(commands[1], ["issue", "close", URL])

    def test_missing_item_is_added_and_read_before_writing(self):
        self.read.side_effect = [("OPEN", None), ("OPEN", None)]
        with self.assertRaisesRegex(RuntimeError, "暂未读到"):
            complete(13, ISSUE, URL, EXPECTED)
        self.write.assert_called_once()
        self.assertEqual(self.write.call_args.args[0][:2], ["project", "item-add"])

    def test_unconfirmed_field_leaves_issue_open(self):
        self.read.side_effect = [("OPEN", {"status": "已完成"}), ("OPEN", {"status": "已完成"})]
        with self.assertRaisesRegex(RuntimeError, "工时"):
            complete(13, ISSUE, URL, EXPECTED)
        self.write.assert_called_once()
        self.assertEqual(self.write.call_args.args[0][:2], ["project", "item-edit"])

    def test_completed_issue_has_no_writes(self):
        self.read.return_value = ("CLOSED", {"hours": 0, "status": "已完成"})
        complete(13, ISSUE, URL, EXPECTED)
        self.write.assert_not_called()
