# Verify Stack Trace — patch flow

This repository includes a small diagnosis pipeline (`diagnose_trace.py`) that parses a stack trace, maps frames to source snippets, and suggests fixes.

New flag: `--run-patch-flow`

- When you pass `--run-patch-flow` to `diagnose_trace.py`, the tool will, for each matched frame, run a small helper flow that:
  1. retrieves top snippets using `find_snippets.py` (writes `snippets.json`)
  2. builds a prioritized LLM prompt using `focus_and_prompt.py` (writes `prompt.txt`)
  3. calls the LLM via `patch_request.py` and saves `llm_raw.txt` and `llm_parsed.json` (if parseable)

Files created by the flow (in `Code/`):
- `snippets.json` — top-k snippets for the matched file/symbol
- `prompt.txt` — the prompt constructed from the trace + snippets
- `llm_raw.txt` — raw LLM output
- `llm_parsed.json` — parsed JSON suggestion when the LLM output is valid JSON

Example usages

- Normal diagnose (no helper flow, offline-first):

```powershell
python diagnose_trace.py --repo "Q:\src\DsMainDev\Sql\xdb" --trace sample_trace.txt --out report.json
```

- Diagnose and run the end-to-end patch flow (will call helper scripts and, if `--use-llm` is set and Azure env vars are configured, the LLM):

```powershell
python diagnose_trace.py --repo "Q:\src\DsMainDev\Sql\xdb" --trace sample_trace.txt --out report_with_patches.json --run-patch-flow --use-llm
```

Notes and tips
- `patch_request.py` will attempt to import your project's `pr_analyzer.llm_client` first, and fall back to a local `llm_client.py` in this `Code/` folder if present.
- The helper flow is intentionally conservative: exceptions in the patch flow are caught and won't abort the main diagnosis run. Inspect `llm_raw.txt` when `llm_parsed.json` is missing.
- Customize the index path in `find_snippets.py` with `--index` if your semantic index is not `demo_index`.

If you want this flow to write per-frame outputs (no overwrites) or to automatically apply patches and run tests, I can add that next.
Verify Stack Trace CLI
======================

Purpose
-------
Small utility to map a .NET stack trace to local repository source files and extract code snippets around reported line numbers. Useful as a quick, repeatable first step before deeper analysis or sending snippets to your analyzer/LLM.

Usage
-----
Run from the workspace (Windows PowerShell):

```powershell
python Code\verify_stack_trace.py --repo "Q:\src\DsMainDev\Sql\xdb" --trace traces\sample_trace.txt --context 6 --out report.json
```

Output
------
JSON array of frames. Each entry may include:
- `frame`: parsed stack frame
- `match`: snippet and path when file+line matched
- `candidates`: list of candidate files when only a symbol was present
- `confidence`: heuristic confidence score

Notes
-----
- This tool is intentionally simple and offline-friendly. It doesn't call remote services.
- For better symbol-only matching, integrate with your analyzer indexer or a language server.
