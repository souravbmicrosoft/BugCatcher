"""focus_and_prompt.py
Given a trace frame and a snippets file, prioritize local snippets and build an LLM prompt
using the repo's analyzer._build_prompt API. Saves the prompt to a file for review.
"""
import json
from pathlib import Path

from pr_analyzer import analyzer, parser


def build_prompt_from_snippets(trace_path: str, snippets_path: str, out_prompt: str, prefer_filename: str = None):
    trace = Path(trace_path).read_text(encoding='utf-8')
    frames = parser.parse_stack_trace(trace)
    if not frames:
        raise SystemExit('No frames parsed from trace')
    frame = frames[0]
    snippets = json.loads(Path(snippets_path).read_text(encoding='utf-8'))
    if prefer_filename:
        local = [s for s in snippets if prefer_filename in s.get('path','')]
        ordered = local + [s for s in snippets if s not in local]
    else:
        ordered = snippets
    prompt = analyzer._build_prompt(frame, ordered[:8])
    Path(out_prompt).write_text(prompt, encoding='utf-8')
    print(f'Prompt written to {out_prompt}')


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--trace', default='sample_trace.txt')
    p.add_argument('--snippets', default='snippets.json')
    p.add_argument('--out', default='prompt.txt')
    p.add_argument('--prefer', help='Prefer snippets containing this filename')
    args = p.parse_args()
    build_prompt_from_snippets(args.trace, args.snippets, args.out, args.prefer)
