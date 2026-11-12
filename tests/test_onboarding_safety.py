"""实际执行本地接入，GitHub 请求使用可审查的替身。"""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "new-project.sh"


@unittest.skipUnless(shutil.which("jq"), "需要接入依赖 jq")
class TestOnboarding(unittest.TestCase):
    def test_resume_preserves_board_and_commits_only_changed_template(self):
        with tempfile.TemporaryDirectory() as path:
            base = pathlib.Path(path)
            repo = base / "repo"
            repo.mkdir()
            fake = base / "gh"
            fake.write_text("""#!/bin/bash
printf '%s\\n' "$*" >> "$TEST_GH_LOG"
case "$*" in
  *'projectV2(number: 13) { id url }'*) echo '{"id":"PVT_existing","url":"https://github.com/users/a/projects/13"}' ;;
  *'fields(first: 50)'*) echo PVT_field ;;
  *'field(name: "Status")'*) echo true ;;
  'label create '*) ;;
  *) exit 1 ;;
esac
""")
            fake.chmod(0o755)
            sleep = base / "sleep"
            sleep.write_text("#!/bin/sh\nexit 0\n")
            sleep.chmod(0o755)
            git = ["git", "-C", str(repo)]
            subprocess.run([*git, "init", "-q"], check=True)
            subprocess.run([*git, "config", "user.name", "Test"], check=True)
            subprocess.run([*git, "config", "user.email", "test@example.test"], check=True)
            (repo / "CLAUDE.md").write_text("## 项目管理（devledger）\nGitHub Project `#13`\n")
            (repo / "AGENTS.md").write_text("Project #__PM_PROJECT__\n")
            (repo / "staged.txt").write_text("unrelated\n")
            subprocess.run([*git, "add", "staged.txt"], check=True)
            result = subprocess.run(
                ["bash", str(SCRIPT), "a/r", "--local", str(repo)], capture_output=True, text=True,
                env={**os.environ, "PATH": f"{base}:{os.environ['PATH']}", "TEST_GH_LOG": str(base / "calls"), "PM_RESUME": ""},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((repo / "AGENTS.md").read_text(), "Project #13\n")
            calls = (base / "calls").read_text()
            self.assertNotIn("updateProjectV2", calls)
            self.assertNotIn("project create", calls)
            self.assertNotIn("projectsV2(first", calls)
            self.assertEqual(subprocess.check_output([*git, "diff", "--cached", "--name-only"], text=True), "staged.txt\n")
