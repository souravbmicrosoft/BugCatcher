import re
from typing import List, Dict

# Support Python, Java, Node, .NET basic frame extraction
PY_FRAME_RE = re.compile(r"\s*File \"(?P<file>[^\"]+)\", line (?P<line>\d+), in (?P<func>\S+)")
JAVA_FRAME_RE = re.compile(r"\s*at (?P<class>[^\(]+)\((?P<file>[^:]+):(?P<line>\d+)\)")
NODE_FRAME_RE = re.compile(r"\s*at (?P<func>[^\s]+) \((?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+)\)")
# Improved C#/.NET frame regex: capture method signature non-greedily until ' in <file>:line <n>'
CS_FRAME_RE = re.compile(r"\s*at (?P<class>[\w\.<>,`\[\]]+)\.(?P<method>.+?) in (?P<file>.+?):line (?P<line>\d+)")


def parse_stack_trace(trace: str) -> List[Dict]:
    frames = []
    for line in trace.splitlines():
        m = PY_FRAME_RE.match(line)
        if m:
            frames.append({"lang": "python", "file": m.group("file"), "line": int(m.group("line")), "func": m.group("func"), "raw": line})
            continue
        m = JAVA_FRAME_RE.match(line)
        if m:
            frames.append({"lang": "java", "file": m.group("file"), "line": int(m.group("line")), "func": m.group("class"), "raw": line})
            continue
        m = NODE_FRAME_RE.match(line)
        if m:
            frames.append({"lang": "node", "file": m.group("file"), "line": int(m.group("line")), "func": m.group("func"), "raw": line})
            continue
        m = CS_FRAME_RE.match(line)
        if m:
            frames.append({"lang": "csharp", "file": m.group("file"), "line": int(m.group("line")), "func": m.group("method"), "raw": line})
            continue
    return frames
