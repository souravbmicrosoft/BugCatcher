from typing import List, Dict, Any
from .parser import parse_stack_trace
from .retriever import retrieve_for_frame
from . import llm


def _build_prompt(frame: Dict[str, Any], snippets: List[Dict]) -> str:
    prompt = (
        "You are an expert senior engineer. Given the following stack frame and code snippets, determine if the root cause is within the repository code or an external dependency.\n\n"
    )
    prompt += f"Stack frame:\n{frame['raw']}\n\n"
    prompt += "Code snippets (file:chunk_index):\n"
    for s in snippets:
        prompt += f"- {s.get('path')}:{s.get('chunk_index')} ->\n{s.get('snippet')[:800].strip()}\n---\n"
    prompt += (
        "\nReply JSON with keys: classification (one of 'code','dependency','unknown'), confidence (0-1), explanation (short), and suggested_fix (short steps).\n"
    )
    return prompt


def analyze_stack_trace(stack_trace: str, index_path: str, top_k: int = 3) -> Dict[str, Any]:
    frames = parse_stack_trace(stack_trace)
    if not frames:
        return {"error": "no frames parsed"}

    frame = frames[0]
    snippets = retrieve_for_frame(index_path, frame["raw"], top_k=top_k)
    prompt = _build_prompt(frame, snippets)
    raw = llm.ask_llm(prompt)

    # attempt to parse LLM response as JSON; if not JSON, wrap in analysis
    import json

    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {"raw_text": raw}

    return {"frame": frame, "snippets": snippets, "analysis": parsed}
