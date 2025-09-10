import os
from pr_analyzer.analyzer import analyze_stack_trace


def test_analyzer_monkeypatch(monkeypatch, tmp_path):
    # create tiny repo
    repo = tmp_path / "repo"
    repo.mkdir()
    f = repo / "a.py"
    f.write_text("def foo():\n    raise ValueError('oops')\n")
    index = tmp_path / "idx"
    os.environ["PR_ANALYZER_UNIT_TEST"] = "1"
    # build index in test mode
    from pr_analyzer.indexer import build_index

    build_index(str(repo), str(index))

    # monkeypatch LLM
    def fake_ask(prompt, temperature=0.0):
        return '{"classification":"code","confidence":0.9,"explanation":"null pointer in foo","suggested_fix":"check None"}'

    monkeypatch.setattr("pr_analyzer.llm.ask_llm", fake_ask)

    res = analyze_stack_trace('  File "a.py", line 1, in foo', str(index), top_k=1)
    assert res["analysis"]["classification"] == "code"
    assert res["analysis"]["confidence"] == 0.9
