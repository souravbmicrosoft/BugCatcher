"""Minimal Azure OpenAI client helper.

Tries to use the `openai` package if available, otherwise falls back to a REST call via requests.
Environment variables used:
- AZURE_OPENAI_ENDPOINT (e.g. https://your-resource-name.openai.azure.com/)
- AZURE_OPENAI_KEY
- AZURE_OPENAI_DEPLOYMENT (deployment name for chat/completions)
"""
from __future__ import annotations

import json
import os
from typing import Optional


def _env_ok() -> bool:
    return bool(os.environ.get('AZURE_OPENAI_ENDPOINT') and os.environ.get('AZURE_OPENAI_KEY') and os.environ.get('AZURE_OPENAI_DEPLOYMENT'))


def call_azure_openai_system_and_user(system: str, user: str, temperature: float = 0.0) -> Optional[str]:
    if not _env_ok():
        return None
    endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
    key = os.environ['AZURE_OPENAI_KEY']
    deployment = os.environ['AZURE_OPENAI_DEPLOYMENT']

    # Prefer openai package if available
    try:
        import openai
        openai.api_type = 'azure'
        openai.api_base = endpoint
        # set to a reasonable api version; change if your deployment requires different
        openai.api_version = '2023-05-15'
        openai.api_key = key
        resp = openai.ChatCompletion.create(
            engine=deployment,
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
            temperature=temperature,
            max_tokens=1500,
        )
        return resp.choices[0].message.content
    except Exception:
        pass

    # Fallback: try HTTP via requests
    try:
        import requests
        url = endpoint.rstrip('/') + f"/openai/deployments/{deployment}/chat/completions?api-version=2023-05-15"
        headers = {"Content-Type": "application/json", "api-key": key}
        payload = {
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature,
            "max_tokens": 1500,
        }
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        r.raise_for_status()
        j = r.json()
        return j['choices'][0]['message']['content']
    except Exception:
        return None
