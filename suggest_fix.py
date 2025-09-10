"""Heuristic fix suggestion module.

This contains very small rules that inspect a code snippet and suggest likely fixes.
Extend this to call an LLM for richer suggestions if you have credentials.
"""
from __future__ import annotations

from typing import Any, Dict, List


def suggest_fixes_for_snippet(snippet: str, meta: Dict[str, Any], use_llm: bool = False) -> List[Dict[str, Any]]:
    """Return a list of simple suggestions. If use_llm=True and Azure env is configured, call the LLM for richer suggestions."""
    suggestions = []
    s = snippet or ""
    # If LLM requested, try to call it
    if use_llm:
        try:
            from llm_client import call_azure_openai_system_and_user
            system = (
                "You are a helpful coding assistant.\n"
                "Respond ONLY with a JSON array of up to 3 suggestion objects.\n"
                "Each suggestion object must have: title (string), description (string), confidence (0-1 float), optional patch (string)\n"
            )
            user = (
                "Given the following code snippet, return JSON-only suggestions. Do NOT include any prose outside the JSON array.\n\n"
                f"CODE:\n```\n{s}\n```\n\n"
                "Return example:\n[ {\"title\": \"...\", \"description\": \"...\", \"confidence\": 0.8, \"patch\": \"--- a/file.cs\n+++ b/file.cs\n@@ -1,3 +1,6 @@\n+fix\" } ]"
            )
            resp = call_azure_openai_system_and_user(system, user, temperature=0.0)
            if resp:
                # Try to parse JSON out of response strictly
                import json
                try:
                    parsed = json.loads(resp)
                    if isinstance(parsed, list):
                        return parsed
                    elif isinstance(parsed, dict):
                        return [parsed]
                except Exception:
                    # attach raw LLM output if parsing fails so we can inspect it later
                    suggestions.append({'title': 'LLM raw output', 'description': 'LLM returned non-JSON output; see raw_output field', 'confidence': 0.5, 'patch': None, 'raw_output': resp})
        except Exception as e:
            suggestions.append({'title': 'LLM call failed', 'description': str(e), 'confidence': 0.0, 'patch': None})

    # Local heuristics fallback
    if 'Enum.ToObject' in s or '(' in s and 'enum' in s.lower():
        suggestions.append({
            'title': 'Defensive enum conversion',
            'description': 'Validate incoming integer values with Enum.IsDefined or try/catch around enum conversion to avoid invalid enum values.',
            'confidence': 0.7,
            'patch': None,
        })
    if 'FiniteStateMachineInvalidActionOutcomeException' in s or 'InvalidActionOutcome' in s:
        suggestions.append({
            'title': 'Improve failure diagnostics',
            'description': 'Include the unexpected value and available target states in the exception message or log to speed debugging.',
            'confidence': 0.8,
            'patch': None,
        })
    if not suggestions:
        suggestions.append({'title': 'Inspect runtime inputs', 'description': 'Confirm the runtime data (inputs/state) that produced the error; may be not related to code changes.', 'confidence': 0.4, 'patch': None})
    return suggestions
