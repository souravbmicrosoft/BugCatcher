import os
from typing import Optional

try:
    # new-style client
    from openai import OpenAI
except Exception:
    OpenAI = None
import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_TYPE = os.getenv("OPENAI_API_TYPE", "openai")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _make_client() -> Optional[object]:
    if OpenAI is None:
        return None
    # client will pick up env vars for api key / base automatically
    client = OpenAI()
    return client


def ask_llm(prompt: str, temperature: float = 0.0) -> str:
    """Ask the configured OpenAI/Azure model. Returns string (raw content).

    This uses the new OpenAI Python client (OpenAI()) which works with both
    OpenAI and Azure OpenAI when environment variables are configured.
    """
    client = None
    try:
        client = _make_client()
        if client is not None:
            messages = [{"role": "user", "content": prompt}]
            resp = client.chat.completions.create(model=MODEL, messages=messages, temperature=temperature, max_tokens=800)
            try:
                return resp.choices[0].message.content
            except Exception:
                d = resp if isinstance(resp, dict) else resp.__dict__
                try:
                    return d["choices"][0]["message"]["content"]
                except Exception:
                    return str(resp)
    except Exception:
        # fall through to REST fallback
        pass

    # Fallback: If Azure/OpenAI base & key are set, call REST endpoint directly (works for Azure OpenAI)
    if OPENAI_API_BASE and OPENAI_API_KEY:
        api_version = os.getenv("OPENAI_API_VERSION", "2023-05-15")
        base = OPENAI_API_BASE.rstrip("/")
        # Azure OpenAI uses deployments path
        url = f"{base}/openai/deployments/{MODEL}/chat/completions?api-version={api_version}"
        headers = {"api-key": OPENAI_API_KEY, "Content-Type": "application/json"}
        payload = {"messages": [{"role": "user", "content": prompt}], "max_tokens": 800, "temperature": temperature}
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        jr = r.json()
        try:
            return jr["choices"][0]["message"]["content"]
        except Exception:
            return str(jr)

    raise RuntimeError("Unable to call OpenAI client or REST endpoint; check your OpenAI/Azure configuration.")
