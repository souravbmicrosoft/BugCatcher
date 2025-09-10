import os
import sys
from pathlib import Path

# Ensure Code directory is on sys.path
CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from diagnose_trace import diagnose


def test_diagnose_simple(tmp_path):
    # create a tiny repo and trace
    repo = tmp_path / 'repo'
    repo.mkdir()
    f = repo / 'File.cs'
    f.write_text('\n'.join([f'// line {i+1}' for i in range(60)]))
    trace = tmp_path / 'trace.txt'
    trace.write_text('System.Exception: boom\n   at My.Namespace.Type.Method(File.cs:10)')

    report = diagnose(trace, repo, since_days=1, context=2)
    assert isinstance(report, list)
    assert report[0]['match']['found'] is True
