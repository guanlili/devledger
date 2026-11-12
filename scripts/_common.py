"""共享工具：限流感知的 gh 调用、GraphQL 封装与值归一（scripts/ 内各脚本公用）。

读操作根据限流响应退避，写操作失败后由调用方读回。
"""
import json
import subprocess
import time


def retry_delay(status, headers, error, attempt):
    """返回下一次读取前等待的秒数，None 表示立即返回错误。"""
    error = error.lower()
    rate_limited = (status == 429 or "rate limit" in error
                    or (status == 403 and (headers.get("x-ratelimit-remaining") == "0"
                                           or "retry-after" in headers)))
    if rate_limited:
        retry_after = headers.get("retry-after", "")
        reset = headers.get("x-ratelimit-reset", "")
        if retry_after.isdecimal():
            return int(retry_after)
        if headers.get("x-ratelimit-remaining") == "0" and reset.isdecimal():
            return max(0, int(reset) - time.time() + 1)
        return 60 * 2 ** attempt
    if status in (408, 500, 502, 503, 504) or error == "timeout":
        return 15 * (attempt + 1)
    if any(message in error for message in ("connection reset", "connection refused", "i/o timeout", "tls handshake timeout")):
        return 15 * (attempt + 1)
    return None


def run(args, retries=5, timeout=180, pace=0):
    """读取可按响应退避。写入调用应传 retries=1，失败后读回再决定是否补写。"""
    include = args[:2] == ["gh", "api"] and "--paginate" not in args and "--jq" not in args
    command = [*args[:2], "--include", *args[2:]] if include else args
    for attempt in range(retries):
        status, headers = None, {}
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            rc, out, err = result.returncode, result.stdout, result.stderr.strip()
        except subprocess.TimeoutExpired:
            rc, out, err = 1, "", "timeout"
        if include and out.startswith("HTTP/"):
            header, _, out = out.partition("\n\n")
            status_line, *lines = header.splitlines()
            status = int(status_line.split()[1])
            for line in lines:
                key, _, value = line.partition(":")
                headers[key.lower()] = value.strip()
        if rc == 0:
            if pace:
                time.sleep(pace)
            return rc, out.strip(), err
        delay = retry_delay(status, headers, err, attempt)
        if delay is None or attempt + 1 == retries:
            return rc, out.strip(), err
        time.sleep(delay)
    return 1, "", "重试次数必须大于 0"


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
