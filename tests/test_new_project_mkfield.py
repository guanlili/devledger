"""mkfield 幂等去重加固锁定：去重读必须走带重试的 gql 直查，查询失败绝不落入创建分支。

背景（2026-11-09 实测）：旧实现用 `gh project field-list ... 2>/dev/null | jq` 做去重，
撞上次级限流时查询输出非 JSON，jq 静默解析失败 → id 为空 → 误判「字段不存在」
→ 重复创建被 GitHub 拒绝 → 脚本在字段阶段崩溃，重跑安全承诺失效。
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "new-project.sh").read_text(encoding="utf-8")


def mkfield_body():
    m = re.search(r"^mkfield\(\) \{.*?^\}", SCRIPT, re.S | re.M)
    assert m, "mkfield 函数不存在"
    # 只看可执行代码：注释里允许提及历史坑，不算使用
    return "\n".join(l for l in m.group(0).splitlines() if not l.lstrip().startswith("#"))


class TestMkFieldDedupHardening(unittest.TestCase):
    def test_dedup_reads_via_gql_not_field_list(self):
        """去重读取不得用裸 gh project field-list（失败时 stdout 无 JSON，jq 静默空转）"""
        body = mkfield_body()
        self.assertNotIn("field-list", body)
        self.assertRegex(body, r"gql ")

    def test_lookup_result_shape_checked(self):
        """去重结果必须形状校验：PVT* 幂等复用；空值走创建；非法值中止（防垃圾 id 被当存在）"""
        self.assertRegex(mkfield_body(), r"case .*in\n.*PVT\*")

    def test_create_path_keeps_retries(self):
        """创建路径保留原重试语义"""
        self.assertIn("field-create", mkfield_body())
        self.assertIn("for attempt in 1 2 3", mkfield_body())


class TestInjectionDedupMarker(unittest.TestCase):
    def test_claude_section_dedup_uses_header_not_url(self):
        """CLAUDE.md 注入幂等标记必须用小节标题；v1.2.1 模板正文已不含 Project URL，
        用 URL 判断会导致重跑时重复追加小节（2026-11-09 实测重复 2 份）"""
        self.assertIn('marker = "## 项目管理（devledger', SCRIPT)
        self.assertNotIn("if url in old", SCRIPT)

    def test_put_file_equality_not_substring(self):
        """put_file 一致性判断必须整串相等；子串包含会把「去重后的新内容恰好是旧文件前缀」
        误判为已存在（2026-11-09 实测：CLAUDE.md 重复小节因此修不掉）"""
        self.assertNotIn("content.strip() in base64", SCRIPT)
        self.assertIn("content.strip() ==", SCRIPT)

    def test_section_replace_preserves_trailing_content(self):
        """小节替换必须截止到下一个顶级标题，不得吃掉用户在小节后追加的内容"""
        self.assertIn('old.find("\\n## ", idx + len(marker))', SCRIPT)
        self.assertIn("tail = old[nxt:].lstrip", SCRIPT)
