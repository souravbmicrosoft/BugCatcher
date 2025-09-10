"""patch_request.py
Generic helper: read a prompt text file and call the project's LLM client to request a JSON-only
fix suggestion. Saves both raw LLM output and parsed JSON (if possible).
"""
import json
from pathlib import Path
import sys
try:
    from pr_analyzer.llm_client import call_azure_openai_system_and_user
except Exception:
    # fallback: try to import llm_client from local Code/ directory
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from llm_client import call_azure_openai_system_and_user
    except Exception:
        raise


SYSTEM = (
    "You are a senior engineer. When asked to analyze code, reply only with JSON matching the schema "
    "{\"patch\": string, \"rationale\": string, \"tests\": [string]}" 
)


def request_patch(prompt_path: str, out_raw: str = 'llm_raw.txt', out_json: str = 'llm_parsed.json'):
    prompt = Path(prompt_path).read_text(encoding='utf-8')
    print('Calling LLM...')
    resp = call_azure_openai_system_and_user(SYSTEM, prompt, temperature=0.2)
    Path(out_raw).write_text(resp, encoding='utf-8')
    print(f'Raw LLM output written to {out_raw}')
    try:
        parsed = json.loads(resp)
        Path(out_json).write_text(json.dumps(parsed, indent=2), encoding='utf-8')
        print(f'Parsed JSON written to {out_json}')
    except Exception:
        print('Failed to parse LLM output as JSON; saved raw output for inspection')


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--prompt', default='prompt.txt')
    p.add_argument('--out-raw', default='llm_raw.txt')
    p.add_argument('--out-json', default='llm_parsed.json')
    args = p.parse_args()
    request_patch(args.prompt, args.out_raw, args.out_json)
