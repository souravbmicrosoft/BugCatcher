#!/usr/bin/env python3
"""Generic stack-trace diagnosis pipeline.

Usage:
  python diagnose_trace.py --repo <path> --trace <tracefile> [--since 30] [--context 6] [--out report.json]

What it does:
  - Parses a stack trace into frames (file+line or symbol-only)
  - Attempts to map frames to repo source files (reads snippets)
  - Scans recent git commits/merge messages to find PRs that touched suspect files
  - Runs simple heuristic fix-suggestion rules and returns possible fixes

This is intentionally modular and offline-first; you can extend `suggest_fix` to call an LLM if desired.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from verify_stack_trace import parse_stack_trace, read_snippet, search_candidates

from git_pr_finder import find_recent_prs_touching_files
from suggest_fix import suggest_fixes_for_snippet
from subprocess import run


@dataclass
class FrameReport:
    raw: str
    symbol: str
    file: Optional[str]
    line: Optional[int]
    match: Dict[str, Any]
    candidates: List[str]
    pr_matches: List[Dict[str, Any]]
    fixes: List[Dict[str, Any]]


def diagnose(trace_path: Path, repo: Path, since_days: int = 30, context: int = 6, use_llm: bool = False, run_patch_flow: bool = False) -> List[Dict[str, Any]]:
    text = trace_path.read_text(encoding='utf-8', errors='ignore')
    frames = parse_stack_trace(text)
    results: List[Dict[str, Any]] = []
    suspect_files = set()
    for fr in frames:
        match = None
        candidates = []
        if fr.get('file'):
            match = read_snippet(repo, fr['file'], fr.get('line') or 1, context=context)
            if match.get('found'):
                suspect_files.add(match['path'])
            else:
                # try basename fallback
                match = read_snippet(repo, os.path.basename(fr['file']), fr.get('line') or 1, context=context)
                if match.get('found'):
                    suspect_files.add(match['path'])
        else:
            candidates = search_candidates(repo, fr.get('symbol') or '')
            for c in candidates:
                suspect_files.add(os.path.join(str(repo), c))

        results.append({
            'frame': fr,
            'match': match or {},
            'candidates': candidates,
            'pr_matches': [],
            'fixes': [],
        })

    # Find PRs touching suspect files
    pr_matches = []
    if suspect_files:
        pr_matches = find_recent_prs_touching_files(str(repo), list(suspect_files), since_days=since_days)

    # Attach PR info and run simple fix suggestions for matched snippets
    for r in results:
        if r['match'].get('found'):
            snippet = r['match'].get('snippet', '')
            r['fixes'] = suggest_fixes_for_snippet(snippet, r['match'], use_llm=use_llm)
            # attach PRs that touched the same file
            path = r['match'].get('path')
            if path:
                r['pr_matches'] = [p for p in pr_matches if p.get('touched_path') == path]
            # optional patch flow: build local snippets, prompt, and call LLM patch_request
            if run_patch_flow:
                try:
                    tmp_frames = Path('frames.json')
                    tmp_frames.write_text(json.dumps([r], indent=2), encoding='utf-8')
                    matched_name = Path(path).name if path else None
                    # run find_snippets -> focus_and_prompt -> patch_request
                    run(['python', 'find_snippets.py', '--index', 'demo_index', '--query', matched_name or Path(path).name, '--out', 'snippets.json', '--top', '12'], check=False)
                    run(['python', 'focus_and_prompt.py', '--trace', str(trace_path), '--snippets', 'snippets.json', '--out', 'prompt.txt', '--prefer', matched_name or ''], check=False)
                    run(['python', 'patch_request.py', '--prompt', 'prompt.txt', '--out-raw', 'llm_raw.txt', '--out-json', 'llm_parsed.json'], check=False)
                except Exception:
                    # don't let patch flow break the main diagnose execution
                    pass
        else:
            # for candidates, attach PRs heuristically
            for c in r['candidates']:
                full = os.path.join(str(repo), c)
                r['pr_matches'].extend([p for p in pr_matches if p.get('touched_path') == full])

    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--trace', required=True)
    ap.add_argument('--since', type=int, default=30, help='How many days of git history to scan')
    ap.add_argument('--context', type=int, default=6)
    ap.add_argument('--out', default=None)
    ap.add_argument('--use-llm', action='store_true', help='If set and Azure OpenAI env is configured, call the LLM for richer fix suggestions')
    ap.add_argument('--run-patch-flow', action='store_true', help='Run snippet->prompt->patch helpers for matched frames and save LLM raw/parsed outputs')
    args = ap.parse_args()

    repo = Path(args.repo)
    trace = Path(args.trace)
    if not repo.exists():
        print('Repo not found:', repo)
        sys.exit(2)
    if not trace.exists():
        print('Trace file not found:', trace)
        sys.exit(2)

    report = diagnose(trace, repo, since_days=args.since, context=args.context, use_llm=args.use_llm, run_patch_flow=args.run_patch_flow)
    out = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(out, encoding='utf-8')
        print('Wrote report to', args.out)
    else:
        print(out)


if __name__ == '__main__':
    main()
