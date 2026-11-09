"""norm() 归一化单测——数字/数字字符串等价（PR #6 引入的行为锁定）。"""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reconcile", ROOT / "scripts" / "reconcile.py")
reconcile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reconcile)
n = reconcile.norm


class TestNorm(unittest.TestCase):
    def test_numeric_equivalence(self):
        for a, b in [(2, 2.0), (2, "2"), ("2.0", 2), (16.0, "16"), (" 2 ", 2), (0, "0")]:
            self.assertEqual(n(a), n(b), f"{a!r} != {b!r}")

    def test_non_numeric_passthrough(self):
        self.assertEqual(n("已完成"), n("已完成"))
        self.assertEqual(n("2026-11-08"), n(" 2026-11-08 "))
        self.assertNotEqual(n("P0"), n("P1"))

    def test_none(self):
        self.assertIsNone(n(None))

    def test_bool(self):
        self.assertEqual(n(True), "true")


if __name__ == "__main__":
    unittest.main()
