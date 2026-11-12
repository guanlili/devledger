"""共享工具：限流感知的 gh 调用、GraphQL 封装与值归一（scripts/ 内各脚本公用）。

设计：单点维护限流策略（主限流按退避、次级限流长睡）；`--value` 通吃字段类型（实测）。
"""
import json
import subprocess
import time


def run(args, retries=5, timeout=180, pace=0):
    """执行命令，失败重试；rate limit 类错误退避 300s，其余线性退避。pace=成功后间歇秒数。"""
    last = ""
    for a in range(retries):
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            r = type("R", (), {"returncode": 1, "stdout": "", "stderr": "timeout"})()
        if r.returncode == 0:
            if pace:
                time.sleep(pace)
            return r.returncode, r.stdout.strip(), r.stderr.strip()
        last = r.stderr.strip()
        if a + 1 < retries:
            time.sleep(300 if "rate limit" in last.lower() else 15 * (a + 1))
    return 1, "", last


def gql(query, retries=5, *, cursor=None):
    """GraphQL 查询 → 解析后的 data；失败返回 None（内部自动退避）。"""
    args = ["gh", "api", "graphql", "-f", "query=" + query]
    if cursor is not None:
        args += ["-f", f"cursor={cursor}"]
    rc, out, _ = run(args, retries=retries)
    if rc != 0:
        return None
    try:
        return json.loads(out)["data"]
    except Exception:
        return None


def norm(v):
    """字段值归一：数字与数字字符串等价，其余按去空白字符串比较（与 read 侧归一规则一致）。"""
    if v is None:
        return None
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, (int, float)):
        f = float(v)
        return str(int(f)) if f.is_integer() else str(f)
    s = str(v).strip()
    try:
        f = float(s)
        return str(int(f)) if f.is_integer() else str(f)
    except ValueError:
        return s
