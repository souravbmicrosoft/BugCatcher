"""find_snippets.py
Generic helper: given a repo/index and a symbol or raw frame text, retrieve top snippets
and save them to a JSON file for downstream prompting.
"""
import json
from pathlib import Path
from pr_analyzer.indexer import search_index

def find_snippets(index_path: str, query: str, out_path: str, top_k: int = 12):
    res = search_index(index_path, query, top_k=top_k)
    Path(out_path).write_text(json.dumps(res, indent=2), encoding='utf-8')
    print(f'Wrote {len(res)} snippets to {out_path}')

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--index', default='demo_index', help='Index dir')
    p.add_argument('--query', required=True, help='Symbol or text to search')
    p.add_argument('--out', default='snippets.json')
    p.add_argument('--top', type=int, default=12)
    args = p.parse_args()
    find_snippets(args.index, args.query, args.out, args.top)
