"""Small utility to scan local git history for merges/PRs touching given files.

This is a heuristic that looks for merge commits in recent history and inspects changed files.
It returns a list of dicts with keys: pr_number (if parseable), commit, subject, touched_path.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from typing import List


MERGE_PR_RE = re.compile(r"Merge (?:pull request|PR|branch).*?(?:#(?P<pr>\d+))|Merged PR (?P<pr2>\d+)")


def _git(cmd: List[str], cwd: str) -> str:
    return subprocess.check_output(['git'] + cmd, cwd=cwd, text=True, errors='ignore')


def find_recent_prs_touching_files(repo_path: str, paths: List[str], since_days: int = 30, max_commits: int = 200):
    # Normalize paths
    abs_paths = {os.path.abspath(p): p for p in paths}
    since = (datetime.now() - timedelta(days=since_days)).isoformat()
    # Get recent merge commits
    try:
        log = _git(['log', f'--since={since}', '--merges', '--pretty=format:%H%x09%s'], cwd=repo_path)
    except Exception:
        return []
    results = []
    for line in log.splitlines():
        if not line.strip():
            continue
        commit, subject = line.split('\t', 1)
        # list files changed in this commit
        try:
            files = _git(['show', '--name-only', '--pretty=format:', commit], cwd=repo_path)
        except Exception:
            continue
        for f in files.splitlines():
            f = f.strip()
            if not f:
                continue
            full = os.path.abspath(os.path.join(repo_path, f))
            if full in abs_paths:
                # try to parse PR number from subject
                m = MERGE_PR_RE.search(subject)
                pr = m.group('pr') if m and m.group('pr') else (m.group('pr2') if m and m.group('pr2') else None)
                results.append({'pr_number': pr, 'commit': commit, 'subject': subject, 'touched_path': full})
    return results
