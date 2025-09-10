import json
import os
import sys
from pathlib import Path

import pytest

# Ensure the parent 'Code' directory is on sys.path so tests can import the module directly.
CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from verify_stack_trace import parse_stack_trace, verify


def test_parse_stack_trace_basic():
    txt = """
System.Exception: boom
   at My.Namespace.Type.Method(File.cs:42)
   at Other.Type.OtherMethod()
"""
    frames = parse_stack_trace(txt)
    assert len(frames) == 2
    assert frames[0]["file"] == "File.cs"
    assert frames[0]["line"] == 42
    assert frames[1]["file"] is None


def test_verify_with_temp_repo(tmp_path):
    # create a small repo tree
    repo = tmp_path / "repo"
    repo.mkdir()
    f = repo / "File.cs"
    f.write_text("\n".join([f"// line {i+1}" for i in range(100)]))

    frames = [{"raw": "at My.Namespace.Type.Method(File.cs:42)", "symbol": "My.Namespace.Type.Method", "file": "File.cs", "line": 42}]
    report = verify(frames, repo, context=3)
    assert isinstance(report, list)
    assert report[0]["match"]["found"] is True
    assert "line 42" in report[0]["match"]["snippet"]
