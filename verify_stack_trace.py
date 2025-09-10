#!/usr/bin/env python3
"""Simple tool to verify a .NET stack trace against a local repo.

Usage:
  python verify_stack_trace.py --repo <path> --trace <tracefile> [--context 6] [--out report.json]

What it does:
  - Parses stack trace lines that look like: at Namespace.Type.Method(File.cs:123)
  - For each frame with file+line info, reads the file in the repo and extracts a context window.
  - For frames without file info, performs a filename/symbol search under the repo to find candidate files.
  - Emits a JSON array of frames with matched file paths, snippets, and basic confidence.

This is intentionally lightweight and deterministic so you can run it offline.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from symbol_map import symbol_to_files

STACK_FRAME_RE = re.compile(r"at\s+(?P<symbol>[\w\.<>`]+)\s*\(?(?P<file>[^:()]+):(?P<line>\d+)\)?")
SYMBOL_ONLY_RE = re.compile(r"at\s+(?P<symbol>[\w\.<>`]+)")


def parse_stack_trace(text: str) -> List[Dict[str, Optional[str]]]:
    frames: List[Dict[str, Optional[str]]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = STACK_FRAME_RE.search(line)
        if m:
            frames.append({
                "raw": line,
                "symbol": m.group("symbol"),
                "file": m.group("file"),
                "line": int(m.group("line")),
            })
            continue
        m2 = SYMBOL_ONLY_RE.search(line)
        if m2:
            frames.append({"raw": line, "symbol": m2.group("symbol"), "file": None, "line": None})
    return frames


def read_snippet(repo: Path, file_path: str, line: int, context: int = 6) -> Dict[str, Any]:
    full = repo / file_path
    if not full.exists():
        return {"found": False, "path": str(full), "snippet": None}
    try:
        with open(full, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        return {"found": False, "path": str(full), "error": str(e)}
    start = max(1, line - context)
    end = min(len(lines), line + context)
    snippet = "".join(lines[start - 1 : end])
    return {"found": True, "path": str(full), "line": line, "start": start, "end": end, "snippet": snippet}


def _score_file_for_symbol(file_path: str, type_token: str, method_token: str, namespace_tokens: List[str]) -> int:
    score = 0
    name = os.path.basename(file_path).lower()
    if type_token and type_token.lower() in name:
        score += 40
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
    except Exception:
        return score
    # class/struct/interface declaration
    if type_token and f'class {type_token.lower()}' in content or (type_token and f'struct {type_token.lower()}' in content):
        score += 30
    # method name occurrence
    if method_token and method_token.lower() in content:
        score += 20
    # namespace tokens
    for t in namespace_tokens:
        if t.lower() in content:
            score += 5
    return score


def search_candidates(repo: Path, symbol: str, max_results: int = 5) -> List[str]:
    # First try symbol map (index or tags)
    try:
        mapped = symbol_to_files(repo, symbol, top_k=max_results)
        if mapped:
            return mapped[:max_results]
    except Exception:
        pass

    # Parse symbol like Namespace.Type.Method or Namespace.Sub.Type.Method
    parts = [p for p in re.split(r"[\.<>`]+", symbol) if p]
    method_token = parts[-1] if parts else ''
    type_token = parts[-2] if len(parts) >= 2 else ''
    namespace_tokens = parts[:-2] if len(parts) > 2 else []

    scores = []
    for root, dirs, files in os.walk(repo):
        for f in files:
            if not f.lower().endswith('.cs'):
                continue
            full = os.path.join(root, f)
            sc = _score_file_for_symbol(full, type_token, method_token, namespace_tokens)
            if sc > 0:
                rel = os.path.relpath(full, repo)
                scores.append((sc, rel))

    # If none scored, fall back to filename contains
    if not scores:
        for root, dirs, files in os.walk(repo):
            for f in files:
                if f.lower().endswith('.cs') and (type_token.lower() in f.lower() or method_token.lower() in f.lower()):
                    scores.append((10, os.path.relpath(os.path.join(root, f), repo)))

    scores.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scores[:max_results]]


def verify(frames: List[Dict[str, Optional[str]]], repo: Path, context: int = 6) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for fr in frames:
        if fr.get("file"):
            # file is often just the filename, but may include path fragments. Try repo-first then raw path.
            file_val = fr["file"]
            # normalize windows-style backslashes
            file_val = file_val.replace('\\', os.sep).replace('/', os.sep)
            # Try both direct path and basename search
            snippet = read_snippet(repo, file_val, fr.get("line") or 1, context=context)
            if not snippet.get("found"):
                # try searching for basename
                snippet = read_snippet(repo, os.path.basename(file_val), fr.get("line") or 1, context=context)
            out.append({"frame": fr, "match": snippet, "confidence": 0.9 if snippet.get("found") else 0.3})
        else:
            # symbol-only: perform candidate search
            cands = search_candidates(repo, fr.get("symbol") or "")
            out.append({"frame": fr, "candidates": cands, "confidence": 0.2 if cands else 0.0})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Path to repository root")
    ap.add_argument("--trace", required=True, help="Path to stack trace file")
    ap.add_argument("--context", type=int, default=6, help="Lines of context to include")
    ap.add_argument("--out", default=None, help="Path to write JSON report")
    args = ap.parse_args()

    repo = Path(args.repo)
    if not repo.exists():
        raise SystemExit(f"Repo path not found: {repo}")
    with open(args.trace, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    frames = parse_stack_trace(text)
    report = verify(frames, repo, context=args.context)
    outp = json.dumps(report, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(outp)
        print(f"Wrote report to {args.out}")
    else:
        print(outp)


if __name__ == '__main__':
    main()
