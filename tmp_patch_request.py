from pr_analyzer import llm
from pathlib import Path

p = Path(r'Q:\src\DsMainDev\Sql\xdb\common\fsm\BaseFiniteStateMachineContext.cs')
lines = p.read_text(encoding='utf-8').splitlines()
start = max(0, 360)
end = min(len(lines), 420)
excerpt = '\n'.join(lines[start:end])

prompt = f"""
You are a helpful senior C# engineer. Below is a code excerpt from `BaseFiniteStateMachineContext.cs` (lines {start+1}-{end}).
A runtime exception is thrown at line 382: FiniteStateMachineInvalidActionOutcomeException when the code checks whether the FSM metadata contains the target state returned by an invoked action.

Task:
1) Diagnose likely root causes in the excerpt in 2-3 bullets.
2) Propose a minimal, safe unified-diff patch (git-style) that either adds defensive checks or improves metadata validation to avoid throwing for valid cases, while retaining correctness. Keep the patch minimal and explain why it's safe.
3) Suggest 2 short unit-test ideas to verify the fix.

Provide output as JSON with keys: "patch" (string containing unified diff), "rationale" (string), "tests" (array of short test descriptions).

Code excerpt:
-----BEGIN EXCERPT-----
{excerpt}
-----END EXCERPT-----

Restrictions: Do not invent other files. Keep changes only inside `BaseFiniteStateMachineContext.cs`. Use conservative edits (null-checks, enum type checks, logging) rather than broad refactors.
"""

print('Calling LLM...')
resp = llm.ask_llm(prompt, temperature=0.2)
print('\nLLM response:\n')
print(resp)
