"""批量推广就绪锁定：标准安装路径引用、AGENTS.md 注入能力、文档与账本示例同步到 6 字段时代。"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
NP = (ROOT / "scripts" / "new-project.sh").read_text(encoding="utf-8")
INSTALL = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
TPL = (ROOT / "assets" / "claude-section.template.md").read_text(encoding="utf-8")
EXPORT = (ROOT / "scripts" / "export-timesheet.py").read_text(encoding="utf-8")


class TestRolloutReadiness(unittest.TestCase):
    def test_skill_doc_six_field_era(self):
        """SKILL.md 应说明 6 字段、9 列并链接避坑指南"""
        self.assertNotIn("5 字段", SKILL)
        self.assertNotIn("View 8 列", SKILL)
        self.assertIn("](references/pitfalls.md)", SKILL)

    def test_templates_use_standard_install_path(self):
        """注入模板必须引用标准安装路径 ~/.agents/skills/devledger（他人机器无 ~/devledger）"""
        self.assertNotIn("~/devledger", TPL)
        agents_tpl = ROOT / "assets" / "agents-section.template.md"
        self.assertTrue(agents_tpl.exists(), "缺 AGENTS.md 注入模板")
        self.assertNotIn("~/devledger", agents_tpl.read_text(encoding="utf-8"))

    def test_new_project_injects_agents_md(self):
        """new-project.sh 必须注入 AGENTS.md（Codex 等读 AGENTS.md 的工具才不是盲区）"""
        self.assertIn("agents-section.template.md", NP)
        self.assertIn("AGENTS.md", NP)

    def test_install_creates_compat_symlink(self):
        """install.sh 建兼容软链 ~/devledger → 标准路径（历史文档与已注入正文仍引用它）"""
        self.assertIn("ln -s", INSTALL)

    def test_example_ledger_has_reqperson(self):
        """示例账本含需求人字段（reconcile 已支持，示例同步）"""
        data = json.loads((ROOT / "references" / "data" / "example-ledger.json").read_text())
        self.assertIn("需求人", data[0]["fields"])

    def test_export_no_dead_code(self):
        """export 中不留 no-op 替换死代码"""
        self.assertNotIn('"query($cursor: String)", "query($cursor: String)"', EXPORT)

    def test_status_options_skip_when_identical(self):
        """坑6:Status 选项重交会清空全部条目已选值——已一致必须跳过 mutation(读回比对)"""
        self.assertIn("已是中文", NP)
        self.assertRegex(NP, r"CURRENT_OPTS=\$\(")