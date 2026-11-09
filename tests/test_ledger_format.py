"""示例账本格式校验。"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestExampleLedger(unittest.TestCase):
    def test_example_ledger_valid(self):
        data = json.loads((ROOT / "references" / "data" / "example-ledger.json").read_text())
        self.assertIsInstance(data, list)
        self.assertTrue(data)
        for e in data:
            self.assertIn("title", e)
            self.assertIn("fields", e)
            self.assertIsInstance(e["fields"], dict)


if __name__ == "__main__":
    unittest.main()
