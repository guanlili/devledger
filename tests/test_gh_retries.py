"""验证 GitHub 响应头优先、永久错误和不盲重试的写入调用。"""
import pathlib
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import _common


class TestGhRetries(unittest.TestCase):
    @patch.object(_common.time, "sleep")
    @patch.object(_common.subprocess, "run")
    def test_retry_after_header_is_honored(self, invoke, sleep):
        invoke.side_effect = [
            subprocess.CompletedProcess([], 1, "HTTP/2.0 403 Forbidden\nRetry-After: 17\n\n{}", "rate limit"),
            subprocess.CompletedProcess([], 0, "HTTP/2.0 200 OK\n\n{}", ""),
        ]
        self.assertEqual(_common.run(["gh", "api", "graphql"]), (0, "{}", ""))
        sleep.assert_called_once_with(17)

    @patch.object(_common.time, "sleep")
    @patch.object(_common.subprocess, "run")
    def test_permission_error_is_immediate(self, invoke, sleep):
        invoke.return_value = subprocess.CompletedProcess([], 1, "HTTP/2.0 403 Forbidden\n\n{}", "Forbidden")
        self.assertEqual(_common.run(["gh", "api", "graphql"])[0], 1)
        invoke.assert_called_once()
        sleep.assert_not_called()

    @patch.object(_common.time, "sleep")
    @patch.object(_common.subprocess, "run")
    def test_mutation_timeout_returns_without_retry(self, invoke, sleep):
        invoke.side_effect = subprocess.TimeoutExpired([], 180)
        self.assertEqual(_common.run(["gh", "project", "item-edit"], retries=1)[2], "timeout")
        invoke.assert_called_once()
        sleep.assert_not_called()
