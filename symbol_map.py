"""Symbol-to-file mapping helpers.

Tries multiple strategies in order:
 - Use a local index metadata file (e.g., demo_index.meta or demo_index.json) if present to map symbols to files.
 - Use a ctags 'tags' file in the repo root if present.
 - Otherwise return an empty list so the caller can fallback to content-based search.

This module is intentionally defensive and optional — it won't fail if FAISS or index files are absent.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional


def _load_index_meta(index_dir: Path) -> Optional[List[dict]]:
    # try common filenames
    candidates = ['demo_index.meta', 'demo_index.json', 'index.meta', 'index.json']
    for name in candidates:
        p = index_dir / name
        if p.exists():
            try:
                txt = p.read_text(encoding='utf-8', errors='ignore')
                # support JSON array
                data = json.loads(txt)
                if isinstance(data, list):
                    return data
            except Exception:
                continue
    return None


def _search_index_meta_for_symbol(index_meta: List[dict], type_token: str, method_token: str) -> List[str]:
    hits = []
    t = type_token.lower() if type_token else ''
    m = method_token.lower() if method_token else ''
    for entry in index_meta:
        # metadata may have 'path' or 'source' fields
        path = entry.get('path') or entry.get('source') or entry.get('file')
        if not path:
            continue
        p = str(path).lower()
        score = 0
        if t and t in p:
            score += 2
        # some indexes include text snippet
        snippet = (entry.get('text') or entry.get('chunk') or '')
        s = snippet.lower() if isinstance(snippet, str) else ''
        if t and f'class {t}' in s:
            score += 5
        if m and m in s:
            score += 3
        if score > 0:
            hits.append((score, path))
    hits.sort(key=lambda x: x[0], reverse=True)
    # return unique paths preserving score order
    seen = set()
    out = []
    for _, p in hits:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _parse_ctags(tags_file: Path, token: str) -> List[str]:
    out = []
    try:
        for line in tags_file.read_text(encoding='utf-8', errors='ignore').splitlines():
            if not line or line.startswith('!'):
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                name = parts[0]
                file = parts[1]
                if token.lower() == name.lower() or token.lower() in name.lower():
                    out.append(file)
    except Exception:
        return []
    return out


def symbol_to_files(repo: Path, symbol: str, index_dir: Optional[Path] = None, top_k: int = 5) -> List[str]:
    """Return candidate relative file paths for the given symbol using available index/tags.

    - repo: Path to repo root
    - symbol: full symbol like Namespace.Type.Method
    - index_dir: optional path where index metadata may live (defaults to repo / 'demo_index' or repo)
    """
    parts = [p for p in __import__('re').split(r'[\.<>`]+', symbol) if p]
    method_token = parts[-1] if parts else ''
    type_token = parts[-2] if len(parts) >= 2 else ''

    # try index metadata
    candidates_dirs = []
    if index_dir:
        candidates_dirs.append(Path(index_dir))
    # common locations
    candidates_dirs.append(repo / 'demo_index')
    candidates_dirs.append(repo)
    for d in candidates_dirs:
        if d.exists():
            meta = _load_index_meta(d)
            if meta:
                files = _search_index_meta_for_symbol(meta, type_token, method_token)
                # normalize to repo-relative if possible
                out = []
                for p in files:
                    try:
                        rp = os.path.relpath(p, repo)
                    except Exception:
                        rp = p
                    out.append(rp)
                return out[:top_k]

    # try ctags/tags file in repo root
    tags = repo / 'tags'
    if tags.exists():
        files = _parse_ctags(tags, type_token or method_token)
        return files[:top_k]

    return []
